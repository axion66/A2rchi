#!/bin/python
import multiprocessing as mp
import os

from flask import Flask

from src.interfaces.chat_app.app import FlaskAppWrapper
from src.utils.yaml_config import load_yaml_config
from src.utils.env import read_secret
from src.utils.logging import setup_logging


def initialize_config_from_yaml(config):
    """Initialize ConfigService from YAML config on startup."""
    try:
        from src.utils.config_service import ConfigService
        
        pg_config = {
            "password": read_secret("PG_PASSWORD"),
            **config["services"]["postgres"],
        }
        
        config_service = ConfigService(pg_config)
        config_service.initialize_from_yaml(config)
        print("Synced configuration to PostgreSQL")
    except Exception as e:
        print(f"Warning: Could not sync config to PostgreSQL: {e}")
        # Non-fatal - service can still start without ConfigService sync


def main():
    
    setup_logging()

    # load secrets
    os.environ['ANTHROPIC_API_KEY'] = read_secret("ANTHROPIC_API_KEY")
    os.environ['OPENAI_API_KEY'] = read_secret("OPENAI_API_KEY")
    os.environ['HUGGING_FACE_HUB_TOKEN'] = read_secret("HUGGING_FACE_HUB_TOKEN")
    
    config = load_yaml_config()
    
    # Initialize ConfigService from YAML (syncs static config to DB)
    initialize_config_from_yaml(config)
    
    chat_config = config["services"]["chat_app"]
    archi_config = config["archi"]
    print(f"Starting Chat Service with (host, port): ({chat_config['host']}, {chat_config['port']})")
    print(f"Accessible externally at (host, port): ({chat_config['hostname']}, {chat_config['external_port']})")

    generate_script(chat_config, archi_config)
    app = FlaskAppWrapper(Flask(
        __name__,
        template_folder=chat_config["template_folder"],
        static_folder=chat_config["static_folder"],
    ))
    app.run(debug=True, use_reloader=False, port=chat_config["port"], host=chat_config["host"])


def generate_script(chat_config, archi_config):
    """
    This is not elegant but it creates the javascript file from the template using the config.yaml parameters
    """
    script_template = os.path.join(chat_config["static_folder"], "script.js-template")
    with open(script_template, "r") as f:
        template = f.read()

    filled_template = template.replace('XX-NUM-RESPONSES-XX', str(chat_config["num_responses_until_feedback"]))
    filled_template = filled_template.replace('XX-TRAINED_ON-XX', str(archi_config["agent_description"]))

    script_file = os.path.join(chat_config["static_folder"], "script.js")
    with open(script_file, "w") as f:
        f.write(filled_template)

    return

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()

