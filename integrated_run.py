import os
import subprocess
import sys

def run_command(command, cwd=None):
    """Run a shell command and print its output."""
    print(f"\n> Running: {command} in {cwd or '.'}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=cwd
    )
    for line in process.stdout:
        print(line, end="")
    process.wait()
    return process.returncode

def main():
    print("=== MF Chatbot Integrated Pipeline ===")
    
    # 1. Check for Scraping
    data_path = os.path.join("Phase_1", "fund_data.json")
    if not os.path.exists(data_path):
        print("\n[Phase 1] fund_data.json not found. Starting Scraper...")
        ret = run_command("python scraper.py", cwd="Phase_1")
        if ret != 0:
            print("Error: Scraping failed. Please check Phase_1/scraper.py")
            return
    else:
        print("\n[Phase 1] Scraping skipped: fund_data.json already exists.")

    # 2. Check for Ingestion
    db_path = os.path.join("Phase_2", "chroma_db")
    if not os.path.exists(db_path):
        print("\n[Phase 2] ChromaDB not found. Starting Ingestion...")
        # Ensure Phase 2 can find its .env or use root
        ret = run_command("python ingestion.py", cwd="Phase_2")
        if ret != 0:
            print("Error: Ingestion failed. Please check Phase_2/ingestion.py")
            return
    else:
        print("\n[Phase 2] Ingestion skipped: ChromaDB already exists.")

    # 3. Launch UI
    print("\n[Phase 3/4] Launching Streamlit UI...")
    print("Visit: http://localhost:8501")
    run_command("streamlit run Phase_3/app.py")

if __name__ == "__main__":
    main()
