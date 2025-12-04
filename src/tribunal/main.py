import asyncio
import os
from typing import List, Dict

from nicegui import ui, app
from openai import AsyncOpenAI

# --- Configuration ---
# Parallax API Configuration
# Ensure your local Parallax/vLLM is running on this port
PARALLAX_API_BASE = "http://localhost:3001/v1" 
PARALLAX_API_KEY = "EMPTY"
MODEL_NAME = "dolphin-2.9.2-qwen2-7b-4bit" # Updated to uncensored model

# --- Visual Style Constants ---
THEME_BG = "#050505"
THEME_TEXT_MAIN = "#00ff00" # Terminal Green
THEME_TEXT_ERROR = "#ff0000" # Blood Red
THEME_FONT = "'Courier New', Courier, monospace"

# --- CSS ---
# Global CSS for the Cyberpunk/Brutalist look
GLOBAL_CSS = f"""
    body {{
        background-color: {THEME_BG};
        color: {THEME_TEXT_MAIN};
        font-family: {THEME_FONT};
    }}
    .nicegui-content {{
        padding: 0;
        margin: 0;
        max-width: 100%;
    }}
    .q-card {{
        background-color: #0a0a0a;
        border: 1px solid {THEME_TEXT_MAIN};
        border-radius: 0px !important;
        box-shadow: none;
    }}
    .q-btn {{
        border-radius: 0px !important;
        border: 1px solid {THEME_TEXT_MAIN};
        color: {THEME_TEXT_MAIN};
        background: transparent;
    }}
    .q-btn:hover {{
        background: {THEME_TEXT_MAIN};
        color: {THEME_BG};
    }}
    .q-field__native, .q-field__input {{
        color: {THEME_TEXT_MAIN} !important;
        font-family: {THEME_FONT};
    }}
    .q-field__control {{
        border-radius: 0px !important;
    }}
    .q-field--outlined .q-field__control:before {{
        border: 1px solid {THEME_TEXT_MAIN};
    }}
    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: {THEME_BG}; 
    }}
    ::-webkit-scrollbar-thumb {{
        background: {THEME_TEXT_MAIN}; 
    }}
    
    /* Custom classes */
    .tribunal-card-header {{
        border-bottom: 1px solid {THEME_TEXT_MAIN};
        padding: 8px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}
    .tribunal-verdict {{
        border-color: {THEME_TEXT_ERROR} !important;
        color: {THEME_TEXT_ERROR} !important;
    }}
    .tribunal-verdict .tribunal-card-header {{
        border-bottom-color: {THEME_TEXT_ERROR};
        color: {THEME_TEXT_ERROR};
    }}
"""

# --- System Prompts ---
PROMPT_FEMINIST = """
You are Agent A, a Radical Feminist Theorist in the style of Bell Hooks. 
Analyze the user's confession strictly through the lens of gender power dynamics, patriarchy, and intersectionality.
Be harsh, critical, and uncompromising. Do not offer comfort. Expose the hidden gender bias.
"""

PROMPT_MARXIST = """
You are Agent B, a Marxist Theorist in the style of Theodor Adorno.
Analyze the user's confession strictly through the lens of late-stage capitalism, commodity fetishism, and alienation.
Be cold, analytical, and detached. View the user as a symptom of a sick system.
"""

PROMPT_BIOLOGICAL = """
You are Agent C, a Biological Essentialist/Evolutionary Psychologist.
Analyze the user's confession strictly through the lens of evolutionary drives, mating strategies, and resource acquisition.
Be cynical, reductive, and focus on primal instincts. Dismiss higher meaning.
"""

PROMPT_JUDGE = """
You are The High Judge of the Digital Tribunal.
Review the user's confession and the three conflicting analyses provided by your agents.
Synthesize these into a Final Verdict.
Your tone should be authoritative, final, and crushing.
Pronounce a sentence or a "penance" for the user.
"""

# --- Logic ---

# --- Logic ---

class TribunalAgent:
    def __init__(self, name: str, system_prompt: str, ui_container: ui.scroll_area):
        self.name = name
        self.system_prompt = system_prompt
        self.ui_container = ui_container
        self.client = AsyncOpenAI(base_url=PARALLAX_API_BASE, api_key=PARALLAX_API_KEY)
        self.last_verdict = "" # Store the last verdict for context
        self.interrogation_btn = None # Reference to the button

    async def analyze(self, confession: str) -> str:
        """
        Sends the confession to the LLM with the specific persona.
        Updates the UI container in real-time.
        """
        full_response = ""
        try:
            # Clear previous content
            self.ui_container.clear()
            
            # Create a label for streaming content
            with self.ui_container:
                response_label = ui.label().classes('whitespace-pre-wrap font-mono text-sm w-full text-left')
            
            response = await self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": confession}
                ],
                stream=True,
                temperature=0.7,
            )

            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    response_label.set_text(full_response)
            
            self.last_verdict = full_response
            # Button activation is now handled by the main orchestration after Final Verdict
            
            return full_response

        except Exception as e:
            error_msg = f"CONNECTION ERROR: {str(e)}"
            with self.ui_container:
                ui.label(error_msg).classes('text-red-500 font-bold')
            return error_msg

async def log_message(message: str, container: ui.scroll_area):
    """Adds a timestamped log message to the sidebar."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    with container:
        ui.label(f"[{timestamp}] {message}").classes('text-xs font-mono text-green-500')
    container.scroll_to(percent=1.0)

# --- Interrogation Room Logic ---
async def open_interrogation_room(agent: TribunalAgent, confession: str):
    """Opens a full-screen dialog for chatting with the specific agent."""
    
    # Dialog Context
    dialog = ui.dialog()
    with dialog, ui.card().classes('w-full h-full bg-black border border-green-500 p-0 no-shadow'):
        with ui.row().classes('w-full h-full no-wrap'):
            # Left Column: Static Context
            with ui.column().classes('w-1/3 h-full border-r border-green-500 p-4'):
                ui.label('CASE FILE').classes('text-2xl font-bold mb-4 text-green-500')
                
                ui.label('SUBJECT CONFESSION:').classes('text-sm font-bold text-green-700 mb-1')
                # Fix 1: Use scroll area and whitespace-pre-wrap for long text
                with ui.scroll_area().classes('w-full h-32 border border-green-900 p-2 mb-4'):
                    ui.label(confession).classes('text-xs font-mono text-green-500 whitespace-pre-wrap w-full break-words')
                
                ui.label(f'INITIAL CHARGE ({agent.name.upper()}):').classes('text-sm font-bold text-green-700 mb-1')
                with ui.scroll_area().classes('w-full flex-grow border border-green-900 p-2'):
                    ui.label(agent.last_verdict).classes('text-xs font-mono text-green-500 whitespace-pre-wrap w-full break-words')
                
                ui.button('TERMINATE SESSION', on_click=dialog.close).classes('w-full mt-4 border border-red-500 text-red-500 hover:bg-red-900')

            # Right Column: Chat Stream
            with ui.column().classes('w-2/3 h-full p-4 flex flex-col'):
                ui.label(f'INTERROGATION LOG // {agent.name.upper()}').classes('text-xl font-bold mb-4 text-green-500 blink')
                
                # Chat Container
                chat_container = ui.scroll_area().classes('w-full flex-grow border border-green-900 p-4 mb-4 bg-black')
                
                # Input Area
                with ui.row().classes('w-full no-wrap gap-2'):
                    chat_input = ui.input(placeholder='ENTER REBUTTAL...').classes('flex-grow border border-green-500 text-green-500 p-1').props('outlined dense')
                    # Use a wrapper function to avoid lambda binding issues
                    async def on_send_click():
                        await send_message()
                    send_btn = ui.button('TRANSMIT', on_click=on_send_click).classes('border border-green-500 text-green-500')

                # Chat Logic
                messages = [
                    {"role": "system", "content": f"{agent.system_prompt}\n\nCONTEXT:\nThe user has entered the interrogation room to discuss their confession: '{confession}'.\nYour previous verdict was: '{agent.last_verdict}'.\nContinue the critique and answer their questions directly. Maintain your persona."}
                ]
                
                async def send_message():
                    user_msg = chat_input.value
                    if not user_msg: return
                    
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    # Fix 2: Terminal Style Chat (No bubbles)
                    with chat_container:
                        ui.label(f"[{timestamp}] SUBJECT:").classes('text-green-700 font-bold text-xs mt-2')
                        ui.label(user_msg).classes('text-green-500 font-mono text-sm whitespace-pre-wrap ml-4')
                    
                    messages.append({"role": "user", "content": user_msg})
                    chat_input.value = ''
                    
                    # Agent Response Placeholder
                    with chat_container:
                        ui.label(f"[{timestamp}] {agent.name.upper()}:").classes('text-red-700 font-bold text-xs mt-2')
                        response_label = ui.label().classes('text-red-500 font-mono text-sm whitespace-pre-wrap ml-4')
                        spinner = ui.spinner(size='sm').classes('text-red-500 ml-4')
                    
                    chat_container.scroll_to(percent=1.0)

                    # Stream Response
                    full_response = ""
                    try:
                        client = AsyncOpenAI(base_url=PARALLAX_API_BASE, api_key=PARALLAX_API_KEY)
                        stream = await client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=messages,
                            stream=True,
                            temperature=0.7
                        )
                        
                        spinner.delete()
                        
                        async for chunk in stream:
                            content = chunk.choices[0].delta.content
                            if content:
                                full_response += content
                                response_label.set_text(full_response)
                                # Fix 3: Scroll to bottom during stream
                                chat_container.scroll_to(percent=1.0)
                        
                        messages.append({"role": "assistant", "content": full_response})
                        
                    except Exception as e:
                        spinner.delete()
                        with chat_container:
                            ui.label(f"ERROR: {e}").classes('text-red-500 font-bold')

                chat_input.on('keydown.enter', send_message)

    dialog.open()


# --- App State ---
class TribunalState:
    def __init__(self):
        self.logs: List[str] = []
        self.is_processing = False

state = TribunalState()

# --- Main UI ---
@ui.page('/')
async def main_page():
    ui.add_head_html(f'<style>{GLOBAL_CSS}</style>')
    
    # Layout
    with ui.row().classes('w-full h-screen no-wrap'):
        # Sidebar
        with ui.column().classes('w-1/3 h-full p-4 border-r border-green-500'):
            ui.label('THE TRIBUNAL').classes('text-4xl font-bold mb-8 glitch-effect')
            
            confession_input = ui.textarea(placeholder='CONFESS YOUR SINS HERE...').classes('w-full h-40 mb-4 bg-transparent border border-green-500 p-2 text-green-500')
            
            submit_btn = ui.button('SUBMIT FOR JUDGMENT').classes('w-full mb-8 border border-green-500 text-green-500 hover:bg-green-500 hover:text-black')
            
            ui.label('SYSTEM LOGS:').classes('mb-2 font-bold')
            log_container = ui.scroll_area().classes('w-full h-full border border-green-500 p-2 bg-black')
            
        # Main Area
        with ui.column().classes('w-2/3 h-full p-4'):
            # Agent Grid
            with ui.grid(columns=3).classes('w-full gap-4 mb-4 h-1/2'):
                # Agent A
                with ui.card().classes('h-full w-full p-0'):
                    with ui.column().classes('w-full h-full gap-0 no-wrap'):
                        ui.label('AGENT A: FEMINIST').classes('tribunal-card-header w-full text-center bg-green-900 text-black')
                        agent_a_container = ui.scroll_area().classes('p-2 w-full flex-grow bg-black border-t border-green-500 text-left')
                        # Interrogation Button
                        btn_a = ui.button('ENTER INTERROGATION', on_click=lambda: open_interrogation_room(agent_a_obj, confession_input.value)).classes('w-full rounded-none border-t border-green-500 text-green-500 hover:bg-green-900')
                        btn_a.disable()
                
                # Agent B
                with ui.card().classes('h-full w-full p-0'):
                    with ui.column().classes('w-full h-full gap-0 no-wrap'):
                        ui.label('AGENT B: MARXIST').classes('tribunal-card-header w-full text-center bg-green-900 text-black')
                        agent_b_container = ui.scroll_area().classes('p-2 w-full flex-grow bg-black border-t border-green-500 text-left')
                        # Interrogation Button
                        btn_b = ui.button('ENTER INTERROGATION', on_click=lambda: open_interrogation_room(agent_b_obj, confession_input.value)).classes('w-full rounded-none border-t border-green-500 text-green-500 hover:bg-green-900')
                        btn_b.disable()

                # Agent C
                with ui.card().classes('h-full w-full p-0'):
                    with ui.column().classes('w-full h-full gap-0 no-wrap'):
                        ui.label('AGENT C: BIOLOGICAL').classes('tribunal-card-header w-full text-center bg-green-900 text-black')
                        agent_c_container = ui.scroll_area().classes('p-2 w-full flex-grow bg-black border-t border-green-500 text-left')
                        # Interrogation Button
                        btn_c = ui.button('ENTER INTERROGATION', on_click=lambda: open_interrogation_room(agent_c_obj, confession_input.value)).classes('w-full rounded-none border-t border-green-500 text-green-500 hover:bg-green-900')
                        btn_c.disable()

            # Verdict Area
            with ui.card().classes('w-full h-1/3 tribunal-verdict mt-4 border-red-500 p-0'):
                with ui.column().classes('w-full h-full gap-0 no-wrap'):
                    ui.label('FINAL VERDICT').classes('tribunal-card-header w-full text-center bg-red-900 text-black font-bold text-xl')
                    verdict_container = ui.scroll_area().classes('p-4 w-full flex-grow bg-black border-t border-red-500 text-red-500 text-lg text-left')

    # --- Orchestration Logic ---
    # Define agent objects globally for the lambda scope (will be initialized in run_tribunal)
    # But we need them for the UI button callbacks. 
    # Better approach: Initialize them with empty containers first, then update containers?
    # Or just pass the containers to the init.
    
    # We need persistent agent objects to store the verdict.
    agent_a_obj = TribunalAgent("Feminist", PROMPT_FEMINIST, agent_a_container)
    agent_a_obj.interrogation_btn = btn_a
    
    agent_b_obj = TribunalAgent("Marxist", PROMPT_MARXIST, agent_b_container)
    agent_b_obj.interrogation_btn = btn_b
    
    agent_c_obj = TribunalAgent("Biological", PROMPT_BIOLOGICAL, agent_c_container)
    agent_c_obj.interrogation_btn = btn_c

    async def run_tribunal():
        confession = confession_input.value
        if not confession:
            await log_message("ERROR: No confession provided.", log_container)
            return

        state.is_processing = True
        submit_btn.disable()
        confession_input.disable()
        
        # Reset Buttons
        btn_a.disable()
        btn_b.disable()
        btn_c.disable()
        
        await log_message("INITIATING TRIBUNAL PROTOCOLS...", log_container)
        
        # Run Agents in Parallel
        await log_message("DEPLOYING AGENTS A, B, C...", log_container)
        
        results = await asyncio.gather(
            agent_a_obj.analyze(confession),
            agent_b_obj.analyze(confession),
            agent_c_obj.analyze(confession)
        )
        
        res_a, res_b, res_c = results
        await log_message("AGENTS REPORTING COMPLETE.", log_container)
        
        # Run Judge
        await log_message("SUMMONING THE HIGH JUDGE...", log_container)
        
        judge_prompt_context = f"""
        CONFESSION: {confession}
        
        AGENT A (Feminist) ANALYSIS: {res_a}
        
        AGENT B (Marxist) ANALYSIS: {res_b}
        
        AGENT C (Biological) ANALYSIS: {res_c}
        """
        
        judge = TribunalAgent("Judge", PROMPT_JUDGE, verdict_container)
        await judge.analyze(judge_prompt_context)
        
        await log_message("JUDGMENT RENDERED. CASE CLOSED.", log_container)
        
        # Enable Interrogation Buttons
        btn_a.enable()
        btn_b.enable()
        btn_c.enable()
        
        state.is_processing = False
        submit_btn.enable()
        confession_input.enable()

    submit_btn.on_click(run_tribunal)

ui.run(title='The Digital Tribunal', dark=True, port=8081)
