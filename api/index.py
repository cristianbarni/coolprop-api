from flask import Flask, request
import json
from CoolProp.CoolProp import PropsSI
import ast
import operator

def safeEval(expr):
    # Map allowed operators to their functional counterparts
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,  # Allows for negative numbers like -5
    }

    def _eval(node):
        if isinstance(node, ast.Num):  # <--- Support for older Python versions
            return node.n
        elif isinstance(node, ast.Constant): # <--- Support for Python 3.8+
            if not isinstance(node.value, (int, float)):
                raise TypeError(f"Unsupported type: {type(node.value).__name__}")
            return node.value
        elif isinstance(node, ast.BinOp):  # <--- Binary operations (e.g., 2 + 2)
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp): # <--- Unary operations (e.g., -5)
            return operators[type(node.op)](_eval(node.operand))
        else:
            raise TypeError(f"Unsupported operation: {type(node).__name__}")

    try:
        # Parse the expression into an AST
        tree = ast.parse(expr, mode='eval')
        return _eval(tree.body)
    except Exception as e:
        return f"Error: {e}"

app = Flask(__name__)

fluids = [
    'R290',
    'R600',
    'R600a',
    'R404A',
    'R134a',
    'R1234yf',
    'R170',
]
properties = {
    'T': {'desc': 'Temperature',
          'units':
          {
              '°C': {'mult': 1, 'off': 273.15},
              '°F': {'mult': 5/9, 'off': -32*5/9+273.15},
              'K': {'mult': 1, 'off': 0},
              'R': {'mult': 9/5, 'off': 0},
          }},
    'P': {'desc': 'Pressure', 'units':
          {
              'Pa (a)': {'mult': 1, 'off': 0},
              'Pa (g)': {'mult': 1, 'off': 101325},
              'kPa (a)': {'mult': 1000, 'off': 0},
              'kPa (g)': {'mult': 1000, 'off': 101325},
              'MPa (a)': {'mult': 1000000, 'off': 0},
              'MPa (g)': {'mult': 1000000, 'off': 101325},
              'bar (a)': {'mult': 100000, 'off': 0},
              'bar (g)': {'mult': 100000, 'off': 101325},
              'atm (a)': {'mult': 101325, 'off': 0},
              'atm (g)': {'mult': 101325, 'off': 101325},
              'psi (a)': {'mult': 6894.76, 'off': 0},
              'psi (g)': {'mult': 6894.76, 'off': 101325},
              'inHg (a)': {'mult': 3386.39, 'off': 0},
              'inHg (g)': {'mult': 3386.39, 'off': 101325},
              'mmHg (a)': {'mult': 760, 'off': 0},
              'mmHg (g)': {'mult': 760, 'off': 101325},
          }},
    'H': {'desc': 'Enthalpy', 'units':
          {
              'J/kg': {'mult': 1, 'off': 0},
              'kJ/kg': {'mult': 1000, 'off': 0},
              'cal/kg': {'mult': 4.184, 'off': 0},
              'kcal/kg': {'mult': 4184, 'off': 0},
          }},
    'D': {'desc': 'Density', 'units': {'kg/m3': {'mult': 1, 'off': 0}}},
    'S': {'desc': 'Entropy', 'units': {'J/kg-K': {'mult': 1, 'off': 0}}},
    'Q': {'desc': 'Vapor quality', 'units': {'-': {'mult': 1, 'off': 0}}},
    'C': {'desc': 'Specific heat (Cp)', 'units': {'J/kg-K': {'mult': 1, 'off': 0}}},
    'O': {'desc': 'Specific heat (Cv)', 'units': {'J/kg-K': {'mult': 1, 'off': 0}}},
    'U': {'desc': 'Internal energy', 'units': {'J/kg': {'mult': 1, 'off': 0}}},
    'V': {'desc': 'Viscosity', 'units': {'Pa-s': {'mult': 1, 'off': 0}}},
    'L': {'desc': 'Thermal conductivity', 'units': {'W/m-K': {'mult': 1, 'off': 0}}},
}


@app.route('/')
def home():

    fluid_options = "".join([f'<option value="{f}">{f}</option>' for f in fluids])
    property_options = "".join([f'<option value="{k}">{v["desc"]}</option>' for k,
                               v in sorted(properties.items(), key=lambda item: item[1]["desc"])])
    properties_json = json.dumps(properties)

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
        <label>Fluid(s):</label>
        <div style="display: flex; align-items: flex-start;">
            <div id="fluid-container" style="display: flex; flex-direction: column; gap: 5px; flex-grow: 1;">
            </div>
            <button type="button" id="add-fluid-btn" style="margin-left: 5px; padding: 5px 10px;">+</button>
        </div>

        <label for="output_type">Output Property:</label>
        <div style="display: flex; gap: 5px;">
            <select id="output_type" name="output_type" style="flex-grow: 1;">{property_options}</select>
            <select id="output_unit" name="output_unit" style="width: 90px;"></select>
        </div>

        <label for="input_type1">Input Property 1:</label>
        <select id="input_type1" name="input_type1">{property_options}</select>

        <label for="input_value1">Input Value 1:</label>
        <div style="display: flex; gap: 5px;">
            <input type="text" id="input_value1" name="input_value1" required placeholder="e.g., 300 or 273.15+20" style="flex-grow: 1;">
            <select id="input_unit1" name="input_unit1" style="width: 90px;"></select>
        </div>

        <label for="input_type2">Input Property 2:</label>
        <select id="input_type2" name="input_type2">{property_options}</select>

        <label for="input_value2">Input Value 2:</label>
        <div style="display: flex; gap: 5px;">
            <input type="text" id="input_value2" name="input_value2" required placeholder="e.g., 101325 or 1.013e5" style="flex-grow: 1;">
            <select id="input_unit2" name="input_unit2" style="width: 90px;"></select>
        </div>

        <button type="submit">Calculate</button>
    </form>
    
    <div id="result-container">
        <h2>Result:</h2>
        <pre id="result">The result will be shown here.</pre>
    </div>

    <script>
        const properties = {properties_json};
        const fluidOptionsHTML = `{fluid_options}`;

        function updateUnits(typeSelectId, unitSelectId) {{
            const typeSelect = document.getElementById(typeSelectId);
            const unitSelect = document.getElementById(unitSelectId);
            const selectedType = typeSelect.value;
            const propData = properties[selectedType];

            unitSelect.innerHTML = '';

            if (propData && propData.units) {{
                for (const unit in propData.units) {{
                    const option = document.createElement('option');
                    option.value = unit;
                    option.textContent = unit;
                    unitSelect.appendChild(option);
                }}
            }} else {{
                const option = document.createElement('option');
                option.value = '-';
                option.textContent = '-';
                unitSelect.appendChild(option);
            }}
        }}

        document.getElementById('input_type1').addEventListener('change', () => updateUnits('input_type1', 'input_unit1'));
        document.getElementById('input_type2').addEventListener('change', () => updateUnits('input_type2', 'input_unit2'));
        document.getElementById('output_type').addEventListener('change', () => updateUnits('output_type', 'output_unit'));

        // Initialize units
        updateUnits('input_type1', 'input_unit1');
        updateUnits('input_type2', 'input_unit2');
        updateUnits('output_type', 'output_unit');

        // Fluid selection logic
        const fluidContainer = document.getElementById('fluid-container');
        const addFluidBtn = document.getElementById('add-fluid-btn');

        function createFluidRow() {{
            const fluidRow = document.createElement('div');
            fluidRow.className = 'fluid-row';
            fluidRow.style.display = 'flex';
            fluidRow.style.gap = '5px';

            const select = document.createElement('select');
            select.name = 'fluid[]';
            select.className = 'fluid-select';
            select.style.flexGrow = '1';
            select.innerHTML = fluidOptionsHTML;

            const percentageInput = document.createElement('input');
            percentageInput.type = 'number';
            percentageInput.name = 'fluid_percentage[]';
            percentageInput.className = 'fluid-percentage';
            percentageInput.placeholder = '%';
            percentageInput.min = 0;
            percentageInput.max = 100;
            percentageInput.style.width = '60px';
            percentageInput.style.display = 'none';

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.textContent = '-';
            removeBtn.style.padding = '5px 10px';
            removeBtn.addEventListener('click', () => {{
                fluidRow.remove();
                updateFluidInputs();
            }});

            fluidRow.appendChild(select);
            fluidRow.appendChild(percentageInput);
            fluidRow.appendChild(removeBtn);

            return fluidRow;
        }}

        function updateFluidInputs() {{
            const rows = fluidContainer.querySelectorAll('.fluid-row');
            const showPercentages = rows.length > 1;

            rows.forEach((row) => {{
                row.querySelector('.fluid-percentage').style.display = showPercentages ? 'block' : 'none';
                row.querySelector('button[type="button"]').style.display = rows.length > 1 ? 'inline-block' : 'none';
            }});
        }}

        addFluidBtn.addEventListener('click', () => {{
            fluidContainer.appendChild(createFluidRow());
            updateFluidInputs();
        }});

        // Initial fluid row
        fluidContainer.appendChild(createFluidRow());
        updateFluidInputs();

        document.getElementById('propssi-form').addEventListener('submit', async function (e) {{
            e.preventDefault();
            
            const fluidRows = document.querySelectorAll('.fluid-row');
            if (fluidRows.length > 1) {{
                let total = 0;
                document.querySelectorAll('.fluid-percentage').forEach(input => total += Number(input.value));
                if (Math.abs(total - 100) > 0.01) {{
                    const resultDiv = document.getElementById('result');
                    resultDiv.textContent = 'Error: Percentages must sum to 100%. Current sum: ' + total + '%';
                    resultDiv.classList.add('error');
                    return;
                }}
            }}

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
        output_unit = request.args.get('output_unit', type=str)
        input_type1 = request.args.get('input_type1', type=str)
        input_value1_raw = request.args.get('input_value1', type=str)
        input_unit1 = request.args.get('input_unit1', type=str)
        input_type2 = request.args.get('input_type2', type=str)
        input_value2_raw = request.args.get('input_value2', type=str)
        input_unit2 = request.args.get('input_unit2', type=str)
        
        fluids = request.args.getlist('fluid[]')
        percentages = request.args.getlist('fluid_percentage[]')
        if not fluids:
            fluids = [request.args.get('fluid', type=str)] if request.args.get('fluid') else []

        if not all([output_type, input_type1, input_value1_raw, input_type2, input_value2_raw]) or not fluids:
            return "Missing one or more required parameters: output_type, input_type1, input_value1, input_type2, input_value2, fluid.", 400

        # Evaluate expressions safely
        input_value1 = safeEval(input_value1_raw)
        if isinstance(input_value1, str) and input_value1.startswith("Error"):
            return f"Invalid input 1: {input_value1}", 400

        # Apply unit conversion for input 1
        if input_unit1 and input_type1 in properties:
            unit_data = properties[input_type1]['units'].get(input_unit1)
            if unit_data:
                input_value1 = (input_value1 * unit_data['mult']) + unit_data['off']

        input_value2 = safeEval(input_value2_raw)
        if isinstance(input_value2, str) and input_value2.startswith("Error"):
            return f"Invalid input 2: {input_value2}", 400

        # Apply unit conversion for input 2
        if input_unit2 and input_type2 in properties:
            unit_data = properties[input_type2]['units'].get(input_unit2)
            if unit_data:
                input_value2 = (input_value2 * unit_data['mult']) + unit_data['off']

        if len(fluids) > 1:
            if len(percentages) != len(fluids):
                return "Number of fluids and percentages do not match.", 400
            try:
                percs = [float(p) for p in percentages]
            except ValueError:
                return "Invalid percentage values.", 400
            if abs(sum(percs) - 100) > 0.01:
                return f"Percentages must sum to 100. Current sum: {sum(percs)}", 400
            
            fluid_str = "HEOS::" + "&".join([f"{f}[{p/100}]" for f, p in zip(fluids, percs)])
        else:
            fluid_str = fluids[0]

        result = PropsSI(output_type, input_type1, float(input_value1), input_type2, float(input_value2), fluid_str)

        # Apply unit conversion for output
        if output_unit and output_type in properties:
            unit_data = properties[output_type]['units'].get(output_unit)
            if unit_data:
                result = (result - unit_data['off']) / unit_data['mult']

        result = round(result, 2)
        return str(result) + output_unit
    except ValueError as e:
        return f"Invalid input or calculation error: {e}", 400
    except Exception as e:
        return f"An unexpected error occurred: {e}", 500


if __name__ == "__main__":
    app.run(debug=True)
