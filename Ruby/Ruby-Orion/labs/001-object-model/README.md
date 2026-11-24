# EXP-001 · O Modelo de Objetos do Ruby

**Pilar:** Alnitak / Learn  
**Objetivo:** entender objetos, classes, herança e introspecção sem bibliotecas externas.

```sh
ruby labs/001-object-model/example.rb
```

Observe o retorno de `self.class`, `Star.superclass` e `Star.instance_methods(false)`.
Altere a classe para incluir um módulo e experimente `Star.ancestors`.

Este experimento é local, determinístico e não acessa a rede.
