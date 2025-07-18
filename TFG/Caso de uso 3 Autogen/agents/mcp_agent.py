from autogen import AssistantAgent
from typing import Any, Optional, List
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

import asyncio
import concurrent.futures


class MCPAssistantAgent(AssistantAgent):
    """
    Un agente AutoGen con capacidades MCP.
    Permite descubrir y usar tools MCP y acceder a recursos MCP.
    """

    def __init__(
        self,
        name: str,  # Nombre del agente
        system_message: str,  # Mensaje del sistema que define el comportamiento del agente
        mcp_server_command: str,  # Comando para iniciar el servidor MCP
        # Argumentos para el comando del servidor MCP
        mcp_server_args: Optional[List[str]] = None,
        **kwargs,
    ):
        super().__init__(name=name, system_message=system_message, **kwargs)
        self.server_params = StdioServerParameters(  # StdioServerParameters es una clase que define los parámetros de conexión para el servidor MCP.
            command=mcp_server_command, args=mcp_server_args or []
        )

        # Los metodos @self.register_for_llm permiten registrar funciones que pueden ser llamadas por el LLM.
        @self.register_for_llm(description="Read content from a MCP resource")
        async def read_resource(uri: str) -> str:
            try:
                # esta función crea una conexión con el servidor MCP utilizando stdio_client, que es una función que permite la comunicación a través de la entrada/salida estándar.
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        # read_resource es un método de la clase ClientSession que permite leer el contenido de un recurso MCP dado su URI.
                        return await session.read_resource(uri)
            except Exception as e:
                return f"Error reading resource: {str(e)}"

        self.read_resource = read_resource

        @self.register_for_llm(description="Call a tool to perform an operation")
        def call_tool(name: str, args: dict) -> Any:
            # Esta función "wrapper" es síncrona y se la da el resultado a Autogen.
            # Dentro, creamos el coroutine _call_tool() y lo lanzamos en un hilo separado.
            async def _call_tool():
                try:
                    print(f" call_tool iniciado con name={name}, args={args}")
                    async with stdio_client(self.server_params) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            result = await session.call_tool(name, args)

                            if not result:
                                return {"status": "success"}
                            # Normalmente 'result' es una lista de TextContent; devolvemos directamente:
                            return result
                except Exception as e:
                    return f"Error calling tool: {str(e)}"

            # ----- Ejecutamos _call_tool() en un hilo distinto utilizando asyncio.run en ese hilo -----
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                # future_sync será un Future de concurrent.futures
                future_sync = executor.submit(
                    lambda: asyncio.run(_call_tool()))
                # .result() bloquea hasta que termine el hilo, pero esto no interrumpe el loop principal
                return future_sync.result()

        self.call_tool = call_tool

        @self.register_for_llm(description="List available tools")
        def list_tools() -> list[dict]:
            async def _list_tools():
                try:
                    async with stdio_client(self.server_params) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            return await session.list_tools()
                except Exception as e:
                    return [{"error": str(e)}]

            # Esta línea crea un ThreadPoolExecutor para ejecutar tareas en hilos separados.
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future_sync = executor.submit(
                    lambda: asyncio.run(_list_tools()))
                return future_sync.result()

        self.list_tools = list_tools
