from modules.base_conocimiento.models import Rule, Fact

class InferenceEngine:
    def __init__(self):
        # Cargar todos los hechos (constantes) de la base de datos
        self.facts = {fact.clave: fact.valor for fact in Fact.objects.all()}
        # Cargar las reglas activas ordenadas por prioridad
        self.rules = Rule.objects.filter(activo=True).order_by('-prioridad')

    def evaluate_fatigue(self, context_data):
        """
        Evalúa el estado de fatiga de un médico dado su contexto actual.
        """
        # Unificar el contexto con las constantes globales (Hechos)
        eval_context = {**self.facts, **context_data}
        
        # Iniciar fatiga en 0 si no viene dada por el contexto base (ahora siempre debería venir)
        if 'fatigue_index' not in eval_context:
            eval_context['fatigue_index'] = 0

        rules_applied = []

        # Encadenamiento hacia adelante: evaluar todas las reglas
        for rule in self.rules:
            if self._evaluate_condition(rule.condicion, eval_context):
                self._apply_action(rule.accion, eval_context)
                rules_applied.append(rule.nombre)
                
        fatigue_index = eval_context.get('fatigue_index', 0)
        
        # Disponibilidad = 100 - fatiga
        disponibilidad = max(0, 100 - fatigue_index)
        
        # Determinar el semáforo final de disponibilidad
        state = 'VERDE'
        if disponibilidad < 30:
            state = 'ROJO'
        elif disponibilidad <= 60:
            state = 'AMARILLO'
            
        return {
            "fatigue_index": fatigue_index,
            "availability": disponibilidad,
            "state": state,
            "rules_applied": rules_applied,
            "details": f"Calculado correctamente. Base: {context_data.get('fatigue_index', 0)}. Reglas aplicadas: {', '.join(rules_applied) if rules_applied else 'Ninguna'}."
        }

    def _evaluate_condition(self, condition, eval_context):
        try:
            # Soporte para AND lógico
            if 'AND' in condition:
                return all(self._evaluate_condition(c, eval_context) for c in condition['AND'])
            
            # Soporte para OR lógico
            if 'OR' in condition:
                return any(self._evaluate_condition(c, eval_context) for c in condition['OR'])

            field_val = eval_context.get(condition.get('field'))
            op = condition.get('operator')
            val = condition.get('value')
            
            # Si el valor es una referencia a un Hecho (ej. "$MAX_HOURS")
            if isinstance(val, str) and val.startswith('$'):
                val = eval_context.get(val[1:])
                
            if op == '>': return field_val is not None and field_val > val
            if op == '>=': return field_val is not None and field_val >= val
            if op == '==': return field_val == val
            if op == '<=': return field_val is not None and field_val <= val
            if op == '<': return field_val is not None and field_val < val
            if op == 'is_true': return field_val is True
            if op == 'is_false': return field_val is False
        except Exception as e:
            # Si hay error (falta campo o tipos incompatibles), la regla no se cumple
            return False
        return False

    def _apply_action(self, action, eval_context):
        action_type = action.get('type')
        val = action.get('value', 0)
        
        if action_type == 'ADD_FATIGUE':
            eval_context['fatigue_index'] += val
        elif action_type == 'SET_FATIGUE':
            eval_context['fatigue_index'] = val
        elif action_type == 'MULTIPLY_FATIGUE':
            eval_context['fatigue_index'] *= val

