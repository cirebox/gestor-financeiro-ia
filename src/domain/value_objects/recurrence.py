# src/domain/value_objects/recurrence.py
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List
from enum import Enum


class RecurrenceType(str, Enum):
    """Tipos de recorrência de transações."""
    DAILY = "diária"
    WEEKLY = "semanal"
    BIWEEKLY = "quinzenal"
    MONTHLY = "mensal"
    BIMONTHLY = "bimestral"
    QUARTERLY = "trimestral"
    SEMIANNUAL = "semestral"
    ANNUAL = "anual"


@dataclass(frozen=True)
class Recurrence:
    """Value Object que representa uma recorrência de transação."""
    
    type: RecurrenceType
    start_date: datetime
    end_date: Optional[datetime] = None
    day_of_month: Optional[int] = None  # Para recorrências mensais ou superiores
    day_of_week: Optional[int] = None   # Para recorrências semanais (0-6, sendo 0=Segunda)
    occurrences: Optional[int] = None   # Número máximo de ocorrências
    
    def __post_init__(self):
        """Validações adicionais após inicialização."""
        if self.type in [RecurrenceType.MONTHLY, RecurrenceType.BIMONTHLY, 
                        RecurrenceType.QUARTERLY, RecurrenceType.SEMIANNUAL,
                        RecurrenceType.ANNUAL] and self.day_of_month is None:
            # Se não foi especificado um dia do mês, usa o dia da data inicial
            object.__setattr__(self, "day_of_month", self.start_date.day)
            
        if self.type == RecurrenceType.WEEKLY and self.day_of_week is None:
            # Se não foi especificado um dia da semana, usa o dia da data inicial
            # Converte para o formato 0-6 onde 0=Segunda, 6=Domingo
            weekday = self.start_date.weekday()
            object.__setattr__(self, "day_of_week", weekday)
    
    def get_next_occurrence(self, reference_date: Optional[datetime] = None) -> Optional[datetime]:
        """
        Calcula a próxima ocorrência a partir de uma data de referência.
        
        Args:
            reference_date: Data de referência (default: hoje)
            
        Returns:
            Data da próxima ocorrência ou None se não houver mais ocorrências
        """
        if reference_date is None:
            reference_date = datetime.now()
            
        # Se já passou da data final ou atingiu o máximo de ocorrências
        if (self.end_date and reference_date > self.end_date) or \
           (self.occurrences is not None and self.occurrences <= 0):
            return None
            
        # Calcula a próxima data com base no tipo de recorrência
        if self.type == RecurrenceType.DAILY:
            next_date = reference_date.replace(hour=self.start_date.hour, 
                                             minute=self.start_date.minute,
                                             second=0, microsecond=0)
            if next_date <= reference_date:
                next_date = next_date.replace(day=next_date.day + 1)
                
        elif self.type == RecurrenceType.WEEKLY:
            # Calcula próximo dia da semana
            days_ahead = self.day_of_week - reference_date.weekday()
            if days_ahead <= 0:  # Já passou este dia na semana atual
                days_ahead += 7
            next_date = reference_date.replace(hour=self.start_date.hour,
                                               minute=self.start_date.minute,
                                               second=0, microsecond=0) + \
                        datetime.timedelta(days=days_ahead)
                
        elif self.type == RecurrenceType.BIWEEKLY:
            # Similar ao semanal, mas a cada duas semanas
            days_ahead = self.day_of_week - reference_date.weekday()
            if days_ahead <= 0:  # Já passou este dia na semana atual
                days_ahead += 14
            else:
                days_ahead += 7  # Adiciona uma semana extra
            next_date = reference_date.replace(hour=self.start_date.hour,
                                               minute=self.start_date.minute,
                                               second=0, microsecond=0) + \
                        datetime.timedelta(days=days_ahead)
        
        elif self.type == RecurrenceType.MONTHLY:
            # Tenta o mesmo dia no próximo mês
            next_date = self._get_next_month_date(reference_date)
            
        elif self.type == RecurrenceType.BIMONTHLY:
            # Tenta o mesmo dia dois meses depois
            next_date = self._get_next_month_date(reference_date, months=2)
            
        elif self.type == RecurrenceType.QUARTERLY:
            # Tenta o mesmo dia três meses depois
            next_date = self._get_next_month_date(reference_date, months=3)
            
        elif self.type == RecurrenceType.SEMIANNUAL:
            # Tenta o mesmo dia seis meses depois
            next_date = self._get_next_month_date(reference_date, months=6)
            
        elif self.type == RecurrenceType.ANNUAL:
            # Tenta o mesmo dia do mesmo mês no próximo ano
            next_date = reference_date.replace(year=reference_date.year + 1,
                                              month=self.start_date.month,
                                              day=min(self.day_of_month, self._get_last_day_of_month(reference_date.year + 1, self.start_date.month)),
                                              hour=self.start_date.hour,
                                              minute=self.start_date.minute,
                                              second=0, microsecond=0)
            if next_date <= reference_date:
                next_date = next_date.replace(year=next_date.year + 1)
        
        # Verifica se está dentro do limite de data final
        if self.end_date and next_date > self.end_date:
            return None
            
        return next_date
    
    def _get_next_month_date(self, reference_date: datetime, months: int = 1) -> datetime:
        """
        Calcula uma data no próximo mês, respeitando o dia definido na recorrência.
        """
        year = reference_date.year
        month = reference_date.month + months
        
        # Ajusta se passar de dezembro
        while month > 12:
            month -= 12
            year += 1
            
        # Verifica o último dia do mês alvo e ajusta se necessário
        target_day = min(self.day_of_month, self._get_last_day_of_month(year, month))
        
        return datetime(year, month, target_day, 
                      self.start_date.hour, self.start_date.minute, 0)
    
    @staticmethod
    def _get_last_day_of_month(year: int, month: int) -> int:
        """
        Retorna o último dia do mês especificado.
        """
        if month == 12:
            last_date = date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            last_date = date(year, month + 1, 1) - datetime.timedelta(days=1)
        return last_date.day
    
    @classmethod
    def create_monthly(cls, 
                     start_date: datetime, 
                     day_of_month: Optional[int] = None, 
                     end_date: Optional[datetime] = None,
                     occurrences: Optional[int] = None) -> 'Recurrence':
        """
        Cria uma recorrência mensal.
        
        Args:
            start_date: Data inicial
            day_of_month: Dia do mês para a recorrência (1-31)
            end_date: Data final (opcional)
            occurrences: Número de ocorrências (opcional)
            
        Returns:
            Uma instância de Recurrence configurada para recorrência mensal
        """
        return cls(
            type=RecurrenceType.MONTHLY,
            start_date=start_date,
            end_date=end_date,
            day_of_month=day_of_month or start_date.day,
            occurrences=occurrences
        )
        
    @classmethod
    def from_string(cls, frequency: str, start_date: datetime, 
                  end_date: Optional[datetime] = None,
                  occurrences: Optional[int] = None) -> 'Recurrence':
        """
        Cria uma recorrência a partir de uma string de frequência.
        
        Args:
            frequency: String de frequência ('diária', 'semanal', 'mensal', etc.)
            start_date: Data inicial
            end_date: Data final (opcional)
            occurrences: Número de ocorrências (opcional)
            
        Returns:
            Uma instância de Recurrence
        """
        try:
            recurrence_type = RecurrenceType(frequency.lower())
        except ValueError:
            raise ValueError(f"Frequência inválida: {frequency}")
            
        return cls(
            type=recurrence_type,
            start_date=start_date,
            end_date=end_date,
            occurrences=occurrences
        )