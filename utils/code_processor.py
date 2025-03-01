from typing import List, Dict

class CodeProcessor:
    def __init__(self):
        self.supported_extensions = ['.py', '.js', '.java', '.cpp', '.ts', '.html', '.css']

    def combine_context(self, query: str, contexts: List[str]) -> str:
        """
        Combines the query with relevant contexts into a structured prompt.
        """
        context_text = "\n".join(f"Context {i+1}: {ctx}" for i, ctx in enumerate(contexts))
        return f"Query: {query}\n\n{context_text}"

    def process_code(self, code: str) -> str:
        """
        Process the code by removing comments and unnecessary whitespace
        """
        # Remove empty lines and normalize whitespace
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        return '\n'.join(lines)

    def extract_functions(self, code: str) -> List[str]:
        """
        Extracts function definitions from the code.
        """
        functions = []
        lines = code.split('\n')
        current_function = []
        
        for line in lines:
            if line.strip().startswith('def '):
                if current_function:
                    functions.append('\n'.join(current_function))
                current_function = [line]
            elif current_function:
                current_function.append(line)
                
        if current_function:
            functions.append('\n'.join(current_function))
            
        return functions

    def extract_code_segments(self, text: str) -> List[str]:
        """
        Extract code segments from text
        """
        # Basic implementation - can be enhanced based on requirements
        return [text]

    def identify_language(self, filename: str) -> str:
        """
        Identify programming language based on file extension
        """
        extension = filename.lower().split('.')[-1]
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'java': 'java',
            'cpp': 'c++',
            'ts': 'typescript',
            'html': 'html',
            'css': 'css'
        }
        return language_map.get(extension, 'unknown')
