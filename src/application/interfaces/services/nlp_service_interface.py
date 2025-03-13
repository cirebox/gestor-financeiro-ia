# src/application/interfaces/services/nlp_service_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple


class NLPServiceInterface(ABC):
    """Interface para o serviço de processamento de linguagem natural."""
    
    @abstractmethod
    async def analyze(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Analisa um texto em linguagem natural para identificar intenções e entidades.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Uma tupla contendo a intenção identificada e um dicionário de entidades extraídas
        """
        pass