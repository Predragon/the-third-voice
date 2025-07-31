# 🤝 Contributing to The Third Voice AI

We welcome contributors who share our mission of helping families heal through better communication. Your contributions, no matter how small, can make a difference.

## How to Contribute

1.  **Fork the repository**: Click the "Fork" button on the top right of the GitHub page.
2.  **Clone your forked repository**:
    ```bash
    git clone [https://github.com/YOUR_USERNAME/the-third-voice.git](https://github.com/YOUR_USERNAME/the-third-voice.git)
    cd the-third-voice
    ```
3.  **Create a new branch for your feature or bug fix**:
    ```bash
    git checkout -b feature/your-feature-name-or-fix/bug-fix-name
    ```
4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Set up your environment variables**:
    * Create a file `.streamlit/secrets.toml` based on `.streamlit/secrets.toml.template` and fill in your API keys.
    * Ensure your Supabase project is configured with Row Level Security (see below).
6.  **Make your changes**: Write clear, well-commented code.
7.  **Test thoroughly**: Ensure your changes don't break existing functionality. (More detailed testing guidelines will be added soon!)
8.  **Commit your changes**: Write clear and concise commit messages.
9.  **Push to your fork**:
    ```bash
    git push origin feature/your-feature-name-or-fix/bug-fix-name
    ```
10. **Submit a Pull Request (PR)**:
    * Go to your forked repository on GitHub.
    * Click "Compare & pull request" next to your new branch.
    * Provide a clear title and description for your PR.

## Areas We Need Help

We are always looking for contributions in these areas:

* 🎨 **UI/UX Design**: Creating intuitive, mobile-first interfaces that foster healing and empathy.
* 🧠 **Psychology & Behavioral Science**: Integrating insights into relationship dynamics and conflict resolution.
* 🤖 **AI/NLP**: Improving emotional understanding, response generation, and new AI features.
* 📝 **Documentation**: Enhancing user guides, developer documentation, and tutorials.
* 🧪 **Testing**: Writing unit tests, integration tests, and end-to-end tests to ensure robustness.
* 🐛 **Bug Reports**: Identifying and reporting any issues.
* 💡 **Feature Suggestions**: Proposing new ideas to enhance the app.

## Code Style and Principles

* Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code.
* Use meaningful variable and function names.
* Add docstrings for all functions and classes.
* Implement robust error handling.
* Prioritize mobile-first design considerations.
* Every contribution should align with our mission: *"When both people are speaking from pain, someone must be the third voice."*

Thank you for helping us build a tool that prevents heartbreak and helps families heal.
