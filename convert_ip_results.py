import os
import json

def process_files(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    for file_name in os.listdir(input_dir):
        if file_name.endswith(".txt"):
            input_path = os.path.join(input_dir, file_name)
            output_path = os.path.join(output_dir, file_name)
            try:
                with open(input_path, "r", encoding="utf-8") as infile:
                    data = json.load(infile)

                selected_orders = data.get("selected_orders", [])
                visited_aisles = data.get("visited_aisles", [])

                with open(output_path, "w", encoding="utf-8") as outfile:
                    outfile.write(f"{len(selected_orders)}\n")
                    outfile.writelines(f"{order}\n" for order in selected_orders)
                    outfile.write(f"{len(visited_aisles)}\n")
                    outfile.writelines(f"{aisle}\n" for aisle in visited_aisles)
            except:
                print(f"Erro ao processar: {input_path}")
            print(f"Processado: {input_path} -> {output_path}")

# Exemplo de uso
input_directory = "outputs/ip_results"
output_directory = "outputs/ip_results_converted"
process_files(input_directory, output_directory)
