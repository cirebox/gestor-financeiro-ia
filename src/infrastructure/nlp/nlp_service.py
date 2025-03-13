# src/infrastructure/nlp/nlp_service.py
from typing import Dict, Any, Tuple

from src.application.interfaces.services.nlp_service_interface import NLPServiceInterface
from src.infrastructure.nlp.intent_recognizer import IntentRecognizer


class NLPService(NLPServiceInterface):
    """Implementação completa do serviço de processamento de linguagem natural."""
    
    def __init__(self):
        """Inicializa o serviço NLP com um reconhecedor de intenções."""
        self.intent_recognizer = IntentRecognizer()
    
    async def analyze(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Analisa um texto em linguagem natural para identificar intenções e entidades.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Uma tupla contendo a intenção identificada e um dicionário de entidades extraídas
        """
        # Delega a análise para o reconhecedor de intenções
        return await self.intent_recognizer.analyze(text)