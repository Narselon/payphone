from itertools import permutations

def generate_code_yaml():
    codes = ['451', '7464', '9453', '3255']  # Your four codes
    all_perms = list(permutations(codes))
    
    # Create the hidden_connections dictionary
    connections = {}
    for perm in all_perms:
        code = ''.join(perm)  # Combine codes into one string
        connections[code] = "secret_ending"
    
    # Add default connection
    connections["default"] = "hub"
    
    return connections

# Generate and print the YAML structure
if __name__ == "__main__":
    connections = generate_code_yaml()
    print("hidden_connections:")
    for code, scene in connections.items():
        print(f'  "{code}": "{scene}"')