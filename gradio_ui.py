
import gradio as gr
import sys
from app import detect_mood, log_journal, ask_question, load_and_split_pdf, get_or_create_vectordb
from mood_plot import generate_mood_plot  # your plot functions

chunks = load_and_split_pdf("CBT.pdf")
vectordb = get_or_create_vectordb(chunks)

conversation_active = False
mood_detected = None

def chat(user_input, history):
    global conversation_active, mood_detected

    exit_keywords = {"no", "stop", "end", "exit", "quit", "end the convo", "end the conversation"}
    user_input_lower = user_input.strip().lower()

    if user_input_lower in exit_keywords:
        if mood_detected:
            log_journal(mood_detected)
            return history + [[user_input, "Session ended. Your mood has been saved to your journal. Thank you for sharing."]]
        else:
            return history + [[user_input, "Session ended. Thank you for sharing."]]

    if not conversation_active:
        mood_detected = detect_mood(user_input)
        conversation_active = True
        return history + [[user_input, f"I sense you might be feeling *{mood_detected}*. Would you like to talk more about it? (yes/no)"]]
    else:
        if user_input_lower in ["no", "nah", "stop"]:
            log_journal(mood_detected)
            conversation_active = False
            mood_detected = None
            return history + [[user_input, "Thank you for sharing. I've saved your mood to your journal. Take care! 🌱"]]
        else:
            answer = ask_question(vectordb, user_input)
            return history + [[user_input, answer]]

def plot_mood_chart():
    img_path = generate_mood_plot()
    return img_path



def end_server():
    print("Shutting down server...")
    sys.exit()

with gr.Blocks(css="""
    .gr-chatbox {
        background-color: rgba(255,255,255,0.85);
        border-radius: 8px;
    }
""") as demo:

    gr.Markdown("<h1 style='text-align: center; color: white;'>🧘 Mental Health Journaling Assistant</h1>")
    chatbot = gr.Chatbot(elem_id="chatbot", height=400)
    msg = gr.Textbox(placeholder="How are you feeling today?", show_label=False)

    with gr.Row():
        btn_plot1 = gr.Button("Plot Mood Chart")
        btn_end = gr.Button("End Conversation & Stop Server")

    image_output = gr.Image()

    def respond(user_input, chat_history):
        return chat(user_input, chat_history), ""

    # Submit input, update chat, and clear text box by returning empty string for msg
    msg.submit(respond, [msg, chatbot], [chatbot, msg])

    btn_plot1.click(plot_mood_chart, outputs=image_output)

    btn_end.click(end_server)

demo.launch()

