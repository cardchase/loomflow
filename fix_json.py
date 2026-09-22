import json

input_file = r'D:\Project\LoomFlow - Sports\backend\workflows\predictor 3.json'
output_file = r'D:\Project\LoomFlow\predictor_3_fixed.json'

with open(input_file, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix backslashes for JSON parsing
text = text.replace('\\\\', '/')
text = text.replace('\\"', '<ESCAPED_QUOTE>')
text = text.replace('\\', '/')
text = text.replace('<ESCAPED_QUOTE>', '\\"')

try:
    json.loads(text)
    print("Successfully parsed fixed JSON.")
except Exception as e:
    print(f"Still failing: {e}")

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Fixed file saved to {output_file}")
