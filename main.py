import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import PyPDF2
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()


class CVAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CV Analyzer")
        self.root.geometry("800x600")

        # Create main container
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Create widgets
        self.setup_ui()

        # Selected file path
        self.current_file = None

    def setup_ui(self):
        # Job Title Input
        ttk.Label(self.main_frame, text="Job Title:", font=("Helvetica", 12)).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.job_title_entry = ttk.Entry(
            self.main_frame, width=50, font=("Helvetica", 10)
        )
        self.job_title_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        # File selection button
        self.select_btn = ttk.Button(
            self.main_frame, text="Select PDF CV", command=self.select_file
        )
        self.select_btn.grid(row=2, column=0, pady=10)

        # File path label
        self.file_label = ttk.Label(
            self.main_frame,
            text="No file selected",
            wraplength=700,
            font=("Helvetica", 10),
        )
        self.file_label.grid(row=3, column=0, pady=5)

        # Analysis button
        self.analyze_btn = ttk.Button(
            self.main_frame,
            text="Analyze CV",
            command=self.analyze_cv,
            state="disabled",
        )
        self.analyze_btn.grid(row=4, column=0, pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.main_frame, mode="indeterminate", length=600
        )
        self.progress.grid(row=5, column=0, pady=10)

        # Results text area
        self.results_text = tk.Text(
            self.main_frame, height=15, width=70, wrap=tk.WORD, font=("Helvetica", 10)
        )
        self.results_text.grid(row=6, column=0, pady=10)

    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF file"""
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            return " ".join([page.extract_text() for page in reader.pages])

    def analyze_cv_with_gpt(self, cv_text, job_title):
        """Analyze CV using OpenAI's ChatGPT API"""
        prompt = f"""Analyze the following CV for a {job_title} position:

CV Text:
{cv_text}

Please provide a structured analysis with the following sections:
1. Overall Score (out of 100)
2. Strengths (3-4 points specific to the job)
3. Weaknesses (3-4 points for improvement)
4. Potential Interview Questions (4-5 questions to assess the candidate)

Format your response as a JSON object with these exact keys:
{{
    "overall_score": <number>,
    "strengths": [<string>, <string>, ...],
    "weaknesses": [<string>, <string>, ...],
    "potential_questions": [<string>, <string>, ...]
}}

Ensure the analysis is tailored to the specific requirements of a {job_title}."""

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional recruiter and CV analyst.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
            )

            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"API Error: {str(e)}")

    def select_file(self):
        filetypes = (("PDF files", "*.pdf"),)

        filename = filedialog.askopenfilename(
            title="Select PDF CV", filetypes=filetypes
        )

        if filename:
            self.current_file = filename
            self.file_label.config(text=f"Selected: {os.path.basename(filename)}")
            self.analyze_btn.config(state="normal")

    def analyze_cv(self):
        job_title = self.job_title_entry.get().strip()

        if not job_title:
            messagebox.showerror("Error", "Please enter a job title")
            return

        if not self.current_file:
            messagebox.showerror("Error", "Please select a CV file")
            return

        # Clear previous results
        self.results_text.delete(1.0, tk.END)

        # Start progress bar
        self.progress.start()
        self.analyze_btn.config(state="disabled")

        try:
            # Extract text from CV
            cv_text = self.extract_text_from_pdf(self.current_file)

            # Analyze CV with GPT
            analysis_json = self.analyze_cv_with_gpt(cv_text, job_title)

            # Parse JSON response
            analysis = json.loads(analysis_json)

            # Format results
            results = f"""CV Analysis for {job_title}:
            
Overall Score: {analysis['overall_score']}/100

Strengths:
{''.join(['• ' + s + '\n' for s in analysis['strengths']])}

Weaknesses:
{''.join(['• ' + w + '\n' for w in analysis['weaknesses']])}

Potential Interview Questions:
{''.join(['• ' + q + '\n' for q in analysis['potential_questions']])}
"""

            # Display results
            self.results_text.insert(tk.END, results)

        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            # Stop progress bar and re-enable button
            self.progress.stop()
            self.analyze_btn.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = CVAnalyzerApp(root)
    root.mainloop()
