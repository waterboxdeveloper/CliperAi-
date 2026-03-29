# FEATURE: Migración Gemini → Claude

**Objetivo**: Reemplazar Gemini con Claude 3.5 Sonnet (sin límites diarios)

**Tiempo estimado**: 1.5 horas
**Complejidad**: Media
**Impacto**: Alto (elimina problema de Gemini quota)

---

## 📋 Pasos del Plan

### ✅ Paso 1: Instalar langchain-anthropic (15 min)
- [ ] `01-install-dependencies.md`
- [ ] Agregar langchain-anthropic a pyproject.toml
- [ ] Ejecutar `uv sync`
- [ ] Crear ANTHROPIC_API_KEY en .env

### ✅ Paso 2: Cambiar imports en copys_generator (10 min)
- [ ] `02-change-imports.md`
- [ ] Reemplazar ChatGoogleGenerativeAI con ChatAnthropic
- [ ] Actualizar imports de langchain

### ✅ Paso 3: Cambiar inicialización del modelo (15 min)
- [ ] `03-update-model-init.md`
- [ ] Cambiar parámetros (model, temperature, max_tokens)
- [ ] Ajustar para Claude 3.5 Sonnet

### ✅ Paso 4: Validar compatibilidad (20 min)
- [ ] `04-validate-compatibility.md`
- [ ] Verificar que prompts funcionan con Claude
- [ ] Testing con clip pequeño
- [ ] Comparar output Gemini vs Claude

### ✅ Paso 5: Testing y rollback (30 min)
- [ ] `05-testing-and-fallback.md`
- [ ] Tests unitarios
- [ ] Tests de integración
- [ ] Fallback a Gemini si falla

### ✅ Paso 6: Finalizar y documentar (10 min)
- [ ] `06-finalize.md`
- [ ] Limpiar código Gemini
- [ ] Actualizar documentación
- [ ] Verificar todo funciona

---

## 🎯 Antes vs Después

### Antes (Gemini)
```
- Tier gratuito: 20 requests/día ❌
- Se agota rápidamente
- Requiere esperar 24h o pagar
```

### Después (Claude)
```
- Sin límite de requests por día ✅
- Plan pro: $20/mes con límites muy altos
- Mejor calidad de respuestas
- Mejor contexto window (200K tokens)
```

---

## 💰 Costo Estimado

**Gemini Free**: 20 requests/día → Bloqueado
**Claude Haiku**: $0.80/M tokens → ~$0.023/video
**Claude Sonnet**: $3/M tokens → ~$0.21/video (RECOMENDADO)

---

**¿Comenzar con Paso 1?** Sí/No
