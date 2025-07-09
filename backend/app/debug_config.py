# File: app/debug_config.py
"""
Debug script to check configuration and environment
"""
import os
from pathlib import Path


def debug_env_config():
    """Debug environment configuration"""
    print("🔍 DEBUGGING ENVIRONMENT CONFIGURATION")
    print("=" * 50)

    # Check current directory
    print(f"📁 Current directory: {os.getcwd()}")

    # Check if .env file exists
    env_files = [".env", "../.env", "../../.env"]
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"✅ Found .env file: {os.path.abspath(env_file)}")

            # Read and display (masked) content
            with open(env_file, "r") as f:
                content = f.read()
                print(f"📄 .env file content:")
                for line in content.split("\n"):
                    if line.strip() and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            if "key" in key.lower() or "secret" in key.lower():
                                masked_value = (
                                    f"{value[:5]}...{value[-5:]}"
                                    if len(value) > 10
                                    else "***"
                                )
                                print(f"   {key}={masked_value}")
                            else:
                                print(f"   {line}")
                        else:
                            print(f"   {line}")
            break
    else:
        print("❌ No .env file found in current or parent directories")

    print("\n🔍 ENVIRONMENT VARIABLES")
    print("-" * 30)

    # Check specific environment variables
    env_vars = [
        "OPENAI_API_KEY",
        "PERPLEXITY_API_KEY",
        "SECRET_KEY",
        "DEBUG",
        "DATABASE_URL",
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            if "key" in var.lower() or "secret" in var.lower():
                masked = f"{value[:5]}...{value[-5:]}" if len(value) > 10 else "***"
                print(f"✅ {var}: {masked} (length: {len(value)})")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")

    print("\n🔍 TRYING TO IMPORT SETTINGS")
    print("-" * 30)

    try:
        from config import settings

        print("✅ Successfully imported settings")

        print(f"🔍 settings.perplexity_api_key: '{settings.perplexity_api_key}'")
        print(
            f"🔍 Length: {len(settings.perplexity_api_key) if settings.perplexity_api_key else 0}"
        )
        print(f"🔍 Type: {type(settings.perplexity_api_key)}")
        print(
            f"🔍 OpenAI key length: {len(settings.openai_api_key) if settings.openai_api_key else 0}"
        )

    except Exception as e:
        print(f"❌ Error importing settings: {e}")

    print("\n🔍 POSSIBLE SOLUTIONS")
    print("-" * 30)
    print("1. Make sure .env file is in the correct directory")
    print("2. Check for extra spaces or quotes around API keys")
    print("3. Restart the server after editing .env")
    print("4. Try setting environment variables directly:")
    print("   export PERPLEXITY_API_KEY=your-key-here")


if __name__ == "__main__":
    debug_env_config()
