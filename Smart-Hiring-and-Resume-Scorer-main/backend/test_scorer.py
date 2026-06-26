import sys
import os

# Add backend dir to pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..', '..', '..', 'Documents', 'coding', 'My Notebook', 'Side projects', 'resume-screener', 'backend')))

try:
    from app.ai.scorer import score_resume
    res = score_resume("Looking for a software engineer with 2 years of Python experience.", "I am a software engineer with 3 years of Python experience. I worked on a big project using React.")
    print("SUCCESS")
    print(res)
except Exception as e:
    print("CRASHED!")
    import traceback
    traceback.print_exc()
