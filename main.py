from config_loader import load_config
import java_scanner

def main():
    config = load_config('config.java.json')
    numeric_references = {}

    # Determine the language and call the appropriate scanner
    if config['language'] == 'Java':
        indexed_data = java_scanner.scan_java_project(config, numeric_references)
        # Process the indexed data or perform further actions as needed

if __name__ == '__main__':
    main()
