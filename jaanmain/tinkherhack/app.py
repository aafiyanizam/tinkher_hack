from flask import Flask, render_template, jsonify, request, send_file
from together import Together
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO

app = Flask(__name__)

# Initialize the Together client
client = Together(api_key='e7a501a28a46881b3559d8599dd96cf6bb100fe303fc4cfa67f02c023b193d41')

# Prompt templates for recipe categories
RECIPE_TEMPLATES = {
    '1': "Generate a quick and easy breakfast recipe using common ingredients. Make it fun and creative!",
    '2': "Create a healthy and delicious lunch recipe that can be prepared in under 30 minutes.",
    '3': "Write a detailed dinner recipe that is perfect for a family meal. Include a unique twist!",
    '4': "Invent a mouth-watering dessert recipe that is both simple and indulgent.",
    '5': "Come up with a tasty snack recipe that is perfect for parties or casual munching."
}

def generate_pdf(recipe_text, filename):
    """Generate a PDF from the recipe text."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Add title
    title = Paragraph("Recipe Generator", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))

    # Add recipe content
    recipe = Paragraph(recipe_text, styles['BodyText'])
    story.append(recipe)

    # Build the PDF
    doc.build(story)

    # Move the buffer's cursor to the beginning
    buffer.seek(0)
    return buffer

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate-recipe', methods=['POST'])
def generate_recipe():
    try:
        data = request.json
        
        # Handle custom prompt
        if 'customPrompt' in data:
            custom_prompt = data['customPrompt']
            prompt = f"Generate a creative and delicious recipe using the following ingredients: {custom_prompt}. Make it easy to follow and include step-by-step instructions."
        # Handle category-based prompt
        elif 'category' in data:
            category = data['category']
            prompt = RECIPE_TEMPLATES.get(category)
        else:
            return jsonify({'error': 'Invalid request. Please provide category or custom ingredients.'}), 400

        # Generate recipe using Together API
        messages = [{"role": "user", "content": prompt}]
        
        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=messages
        )

        if completion and hasattr(completion, 'choices') and len(completion.choices) > 0:
            recipe = completion.choices[0].message.content.strip()
            return jsonify({'recipe': recipe})
        
        return jsonify({'error': 'No recipe generated. Please try again.'}), 500

    except Exception as e:
        print(f"Error: {str(e)}")  # For debugging
        return jsonify({'error': 'An error occurred while generating the recipe.'}), 500

@app.route('/download-recipe-pdf', methods=['POST'])
def download_recipe_pdf():
    try:
        data = request.json
        recipe_text = data.get('recipe')

        if not recipe_text:
            return jsonify({'error': 'No recipe provided for PDF generation.'}), 400

        # Generate the PDF
        pdf_buffer = generate_pdf(recipe_text, "recipe.pdf")

        # Return the PDF as a downloadable file
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name="recipe.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error: {str(e)}")  # For debugging
        return jsonify({'error': 'An error occurred while generating the PDF.'}), 500

if __name__ == '__main__':
    app.run(debug=True)