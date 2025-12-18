import asyncio
import sys
import os
import json
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Configure Gemini
        api_key = os.getenv("asdf")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY (or asdf) not found in .env file")
            
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-3-flash-preview" # Updated to available model

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server"""
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        response = await self.session.list_tools()
        
        # Define tools for Gemini
        tools_list = []
        for tool in response.tools:
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            })

        # Create a chat session with tool definitions
        # Note: In the new SDK, we pass tools config differently.
        # We'll use the 'tool_config' and 'tools' parameter.
        
        # Since dynamic tool definitions from MCP need to be passed precisely,
        # we will construct the list of tool definitions.
        
        # Manually constructing tool definitions for Gemini Client
        gemini_tools = []
        for tool in response.tools:
             gemini_tools.append(types.Tool(
                 function_declarations=[
                     types.FunctionDeclaration(
                         name=tool.name,
                         description=tool.description,
                         parameters=tool.inputSchema
                     )
                 ]
             ))

        # We need to flatten the list of FunctionDeclarations into one Tool object usually,
        # or pass a list of Tools. Let's group all functions into one Tool.
        funcs = []
        for tool in response.tools:
            funcs.append(types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.inputSchema
            ))
            
        tool_obj = types.Tool(function_declarations=funcs)

        # Start chat
        chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                tools=[tool_obj],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True) # We handle execution
            )
        )
        
        # Send message
        response = chat.send_message(query)
        
        final_text = []
        
        # Loop to handle tool calls
        while True:
            # Check for function calls in the response parts
            function_calls = []
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)
                    if part.text:
                         final_text.append(part.text)
            
            if not function_calls:
                break
                
            # Process function calls
            parts_response = []
            
            for call in function_calls:
                tool_name = call.name
                tool_args = call.args
                
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                
                # Execute tool via MCP
                result = await self.session.call_tool(tool_name, tool_args)
                
                # Create function response part
                parts_response.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": result.content}
                    )
                )

            # Send tool results back to the model
            response = chat.send_message(parts_response)
        
        # Collect final text from the last response if any
        if response.text:
             final_text.append(response.text)
             
        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started (Gemini SDK)!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
