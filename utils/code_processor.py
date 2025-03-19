from typing import List, Dict

class CodeProcessor:
    def __init__(self):
        self.supported_extensions = ['.py', '.js', '.java', '.cpp', '.ts', '.html', '.css']
        # Cache for processed code
        self._cache = {}

    def combine_context(self, query: str, contexts: List[str]) -> str:
        """
        Combines the query with relevant contexts into a structured prompt.
        Format the context to be more useful for the LLM.
        """
        processed_contexts = []
        for i, ctx in enumerate(contexts):
            # Process the context to extract relevant parts
            functions = self.extract_functions(ctx)
            cleaned_code = self.process_code(ctx)
            processed_contexts.append(f"Context {i+1}:\n{cleaned_code}\n\nRelevant Functions:\n{functions}")
        
        context_text = "\n\n".join(processed_contexts)
        return f"Query: {query}\n\nRelevant Code Context:\n{context_text}"

    def process_code(self, code: str) -> str:
        """Process code with caching"""
        # Check cache first
        cache_key = hash(code)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Process only if needed
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        processed = '\n'.join(lines)
        
        # Cache result
        self._cache[cache_key] = processed
        return processed

    def extract_functions(self, code: str) -> List[str]:
        """Extract functions with caching"""
        cache_key = hash(code)
        if cache_key in self._cache:
            return self._cache[cache_key]

        functions = []
        current_function = []
        
        for line in code.split('\n'):
            if line.strip().startswith('def '):
                if current_function:
                    functions.append('\n'.join(current_function))
                current_function = [line]
            elif current_function:
                current_function.append(line)
                
        if current_function:
            functions.append('\n'.join(current_function))
            
        self._cache[cache_key] = functions
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
