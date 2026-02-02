from flask import Flask, request
from CoolProp.CoolProp import PropsSI

app = Flask(__name__)


@app.route('/')
def home():
    fluids = ['R290', 'R600', 'R134a', 'R600', 'R170', 'R1234yf', 'R404A']
    properties = {
        'T': 'Temperature in K',
        'P': 'Pressure in Pa',
        'H': 'Enthalpy in J/kg',
        'S': 'Entropy in J/kg-K',
        'D': 'Density in kg/m3',
        'Q': 'Vapor quality',
        'C': 'Specific heat (Cp) in J/kg-K',
        'O': 'Specific heat (Cv) in J;kg-K',
        'U': 'Internal energy in J/kg',
        'V': 'Viscosity in Pa-s',
        'L': 'Thermal conductivity in W/m-K',
        'A': 'Speed of sound in m/s',
        'G': 'Gibbs energy in J/kg'
    }

    fluid_options = "".join([f'<option value="{f}">{f}</option>' for f in fluids])
    property_options = "".join([f'<option value="{k}">{v}</option>' for k,
                               v in sorted(properties.items(), key=lambda item: item[1])])

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CoolProp API</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 2em; background-color: #fdfdfd; color: #333; }}
        h1, h2 {{ color: #111; }}
        form {{ display: grid; grid-template-columns: auto 1fr; gap: 10px; max-width: 500px; margin-bottom: 2em; }}
        label {{ text-align: right; font-weight: bold; }}
        input, select {{ padding: 8px; border-radius: 4px; border: 1px solid #ccc; }}
        button {{ grid-column: 2; justify-self: start; padding: 10px 15px; border: none; background-color: #007bff; color: white; border-radius: 4px; cursor: pointer; }}
        button:hover {{ background-color: #0056b3; }}
        #result-container {{ background-color: #f0f0f0; padding: 15px; border-radius: 4px; }}
        #result {{ font-family: "Courier New", Courier, monospace; font-size: 1.1em; color: #000; white-space: pre-wrap; word-wrap: break-word; }}
        .error {{ color: #d9534f; }}
    </style>
</head>
<body>
    <h1>CoolProp PropsSI Calculator</h1>
    <p>Use this form to calculate a thermophysical property of a fluid.</p>
    <form id="propssi-form">
        <label for="fluid">Fluid:</label>
        <select id="fluid" name="fluid">{fluid_options}</select>

        <label for="output_type">Output Property:</label>
        <select id="output_type" name="output_type">{property_options}</select>

        <label for="input_type1">Input Property 1:</label>
        <select id="input_type1" name="input_type1">{property_options}</select>

        <label for="input_value1">Input Value 1:</label>
        <input type="number" id="input_value1" name="input_value1" step="any" required placeholder="e.g., 300 for Temperature in K">

        <label for="input_type2">Input Property 2:</label>
        <select id="input_type2" name="input_type2">{property_options}</select>

        <label for="input_value2">Input Value 2:</label>
        <input type="number" id="input_value2" name="input_value2" step="any" required placeholder="e.g., 101325 for Pressure in Pa">

        <button type="submit">Calculate</button>
    </form>
    
    <div id="result-container">
        <h2>Result:</h2>
        <pre id="result">The result will be shown here.</pre>
    </div>

    <script>
        document.getElementById('propssi-form').addEventListener('submit', async function (e) {{
            e.preventDefault();
            const form = e.target;
            const formData = new FormData(form);
            const params = new URLSearchParams(formData);
            const resultDiv = document.getElementById('result');
            resultDiv.textContent = 'Calculating...';
            resultDiv.classList.remove('error');

            try {{
                const response = await fetch('/propssi?' + params.toString());
                const resultText = await response.text();
                if (response.ok) {{
                    resultDiv.textContent = resultText;
                }} else {{
                    resultDiv.textContent = 'Error: ' + resultText;
                    resultDiv.classList.add('error');
                }}
            }} catch (error) {{
                resultDiv.textContent = 'Network Error: ' + error;
                resultDiv.classList.add('error');
            }}
        }});
    </script>
</body>
</html>
"""


@app.route('/about')
def about():
    return 'About'


@app.route('/propssi')
def CP_PropsSI():
    try:
        output_type = request.args.get('output_type', type=str)
        input_type1 = request.args.get('input_type1', type=str)
        input_value1 = request.args.get('input_value1', type=float)
        input_type2 = request.args.get('input_type2', type=str)
        input_value2 = request.args.get('input_value2', type=float)
        fluid = request.args.get('fluid', type=str)

        if not all([output_type, input_type1, input_value1 is not None, input_type2, input_value2 is not None, fluid]):
            return "Missing one or more required parameters: output_type, input_type1, input_value1, input_type2, input_value2, fluid.", 400

        result = PropsSI(output_type, input_type1, input_value1, input_type2, input_value2, fluid)
        return str(result)
    except ValueError as e:
        return f"Invalid input or calculation error: {e}", 400
    except Exception as e:
        return f"An unexpected error occurred: {e}", 500


if __name__ == "__main__":
    app.run(debug=True)
