"""
Multi-Agent System для редактирования файлов

Архитектура:
- Supervisor Agent: координирует работу файловых агентов
- File Agents: по одному агенту на каждый загруженный файл
"""

import os
from typing import TypedDict, Annotated, List, Dict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import operator


# Состояние графа
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_file: str
    files: Dict[str, str]  # {filename: content}
    command: str
    result: str


class MultiAgentSystem:
    def __init__(self, api_key: str = None):
        """
        Инициализация multi-agent системы
        
        Args:
            api_key: Google Gemini API ключ
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY не установлен")
        
        # Инициализация LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=self.api_key,
            temperature=0.3
        )
        
        # Граф агентов
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """
        Создание LangGraph workflow для multi-agent системы
        """
        workflow = StateGraph(AgentState)
        
        # Узлы графа
        workflow.add_node("supervisor", self.supervisor_node)
        workflow.add_node("file_agent", self.file_agent_node)
        workflow.add_node("finalize", self.finalize_node)
        
        # Рёбра графа
        workflow.set_entry_point("supervisor")
        
        # Supervisor решает: обработать файл или завершить
        workflow.add_conditional_edges(
            "supervisor",
            self.route_supervisor,
            {
                "file_agent": "file_agent",
                "finalize": "finalize"
            }
        )
        
        # После обработки файла возвращаемся к Supervisor
        workflow.add_edge("file_agent", "supervisor")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def supervisor_node(self, state: AgentState) -> AgentState:
        """
        Supervisor Agent: анализирует команду и решает, какой файл обработать
        """
        messages = state["messages"]
        command = state.get("command", "")
        files = state.get("files", {})
        
        if not command:
            # Первый вызов - получаем команду из последнего сообщения
            if messages and isinstance(messages[-1], HumanMessage):
                command = messages[-1].content
                state["command"] = command
        
        # Supervisor определяет, какой файл нужно обработать
        prompt = f"""Ты - Supervisor Agent в multi-agent системе редактирования файлов.

Команда пользователя: {command}

Доступные файлы: {list(files.keys())}

Определи:
1. Какой файл нужно обработать (верни только имя файла)
2. Если все файлы обработаны или команда неясна, верни "DONE"

Ответь ТОЛЬКО именем файла или DONE, без дополнительного текста."""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        target_file = response.content.strip()
        
        state["current_file"] = target_file
        state["messages"].append(
            AIMessage(content=f"Supervisor: выбран файл '{target_file}'")
        )
        
        return state
    
    def file_agent_node(self, state: AgentState) -> AgentState:
        """
        File Agent: обрабатывает конкретный файл согласно команде
        """
        current_file = state["current_file"]
        command = state["command"]
        files = state["files"]
        
        if current_file not in files:
            state["messages"].append(
                AIMessage(content=f"Ошибка: файл '{current_file}' не найден")
            )
            return state
        
        file_content = files[current_file]
        
        # File Agent применяет изменения к файлу
        prompt = f"""Ты - File Agent, специализирующийся на редактировании файла '{current_file}'.

Текущее содержимое файла:
```
{file_content}
```

Команда пользователя: {command}

Выполни необходимые изменения и верни ТОЛЬКО обновлённое содержимое файла, без дополнительных комментариев."""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        updated_content = response.content.strip()
        
        # Удаляем markdown обёртку, если есть
        if updated_content.startswith("```"):
            lines = updated_content.split("\n")
            updated_content = "\n".join(lines[1:-1]) if len(lines) > 2 else updated_content
        
        # Обновляем содержимое файла
        files[current_file] = updated_content
        state["files"] = files
        
        state["messages"].append(
            AIMessage(content=f"File Agent: файл '{current_file}' обновлён")
        )
        
        # Сохраняем изменения на диск
        self._save_file(current_file, updated_content)
        
        return state
    
    def finalize_node(self, state: AgentState) -> AgentState:
        """
        Финализация: подготовка результата
        """
        state["result"] = "Обработка завершена"
        state["messages"].append(
            AIMessage(content="Все файлы обработаны. Задача выполнена.")
        )
        return state
    
    def route_supervisor(self, state: AgentState) -> str:
        """
        Маршрутизация: определяет следующий шаг после Supervisor
        """
        current_file = state.get("current_file", "")
        
        if current_file == "DONE" or not current_file:
            return "finalize"
        return "file_agent"
    
    def _save_file(self, filename: str, content: str):
        """
        Сохранение файла на диск
        """
        file_path = os.path.join("/app/files", filename)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Ошибка сохранения файла {filename}: {e}")
    
    def process_command(self, command: str, files: Dict[str, str]) -> Dict:
        """
        Обработка команды пользователя
        
        Args:
            command: команда от пользователя
            files: словарь {filename: content}
        
        Returns:
            Результат обработки
        """
        initial_state = AgentState(
            messages=[HumanMessage(content=command)],
            current_file="",
            files=files,
            command=command,
            result=""
        )
        
        # Запускаем workflow
        final_state = self.workflow.invoke(initial_state)
        
        return {
            "status": "success",
            "result": final_state.get("result", ""),
            "updated_files": final_state.get("files", {}),
            "messages": [
                {"role": "ai" if isinstance(m, AIMessage) else "human", 
                 "content": m.content}
                for m in final_state.get("messages", [])
            ]
        }


# Глобальный экземпляр (инициализируется при первом использовании)
_agent_system: MultiAgentSystem = None


def get_agent_system() -> MultiAgentSystem:
    """
    Получить экземпляр multi-agent системы (singleton)
    """
    global _agent_system
    if _agent_system is None:
        _agent_system = MultiAgentSystem()
    return _agent_system
