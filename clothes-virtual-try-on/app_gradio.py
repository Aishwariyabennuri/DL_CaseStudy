import os
import sys
import shutil
from PIL import Image
import gradio as gr
from run import run_pipeline


def try_on(cloth_img, model_img):
    if cloth_img is None or model_img is None:
        raise gr.Error("Please upload both a Cloth image and a Person/Model image.")

    base_dir = os.path.abspath(os.path.dirname(__file__))
    inputs_dir = os.path.join(base_dir, "gradio_inputs")
    test_dir = os.path.join(inputs_dir, "test")
    cloth_dir = os.path.join(test_dir, "cloth")
    image_dir = os.path.join(test_dir, "image")

    # Reset temp inputs
    if os.path.exists(inputs_dir):
        shutil.rmtree(inputs_dir)
    os.makedirs(cloth_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)

    # Save images
    cloth_path = os.path.join(cloth_dir, "cloth.jpg")
    model_path = os.path.join(image_dir, "model.jpg")
    cloth_img.convert("RGB").save(cloth_path, format="JPEG", quality=95)
    model_img.convert("RGB").save(model_path, format="JPEG", quality=95)

    output_dir = os.path.join(base_dir, "gradio_output")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print("\n[GRADIO] Starting Virtual Try-On inference pipeline...")
    res_folder = run_pipeline(inputs_dir=inputs_dir, output_dir=output_dir, checkpoints_dir="checkpoints")

    results = [f for f in os.listdir(res_folder) if f.lower().endswith(('.jpg', '.png'))]
    if results:
        res_img = Image.open(os.path.join(res_folder, results[0]))
        return res_img
    else:
        raise RuntimeError("Inference finished but no output image was found.")


def create_ui():
    custom_css = """
    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .header-text {
        text-align: center;
        margin-bottom: 20px;
    }
    """

    with gr.Blocks(title="AI Virtual Clothes Try-On", css=custom_css) as demo:
        gr.Markdown(
            """
            # 👗 AI Virtual Clothes Try-On
            ### Upload a clothing item and a person photo to virtually try on the outfit!
            *Powered by deep learning: U2Net Cloth Segmentation + SCHP Human Parsing + MediaPipe Pose + ALIAS/GMM Try-on GAN.*
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                cloth_input = gr.Image(type="pil", label="1. Upload Cloth Image (Top/Shirt/Dress)")
                gr.Examples(
                    examples=[
                        "assets/cloth/01260_00.jpg",
                        "assets/cloth/01430_00.jpg",
                        "assets/cloth/02783_00.jpg",
                    ],
                    inputs=cloth_input,
                    label="Sample Clothes"
                )
            with gr.Column(scale=1):
                model_input = gr.Image(type="pil", label="2. Upload Human Image (Full/Upper Body)")
                gr.Examples(
                    examples=[
                        "assets/image/00891_00.jpg",
                        "assets/image/03615_00.jpg",
                        "assets/image/07445_00.jpg",
                    ],
                    inputs=model_input,
                    label="Sample Models"
                )
            with gr.Column(scale=1):
                output_image = gr.Image(type="pil", label="3. Final Try-On Result")

        with gr.Row():
            submit_btn = gr.Button("✨ Run Virtual Try-On", variant="primary", size="lg")

        submit_btn.click(
            fn=try_on,
            inputs=[cloth_input, model_input],
            outputs=[output_image]
        )

    return demo


if __name__ == "__main__":
    app = create_ui()
    print("Launching Gradio app on local server...")
    app.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
