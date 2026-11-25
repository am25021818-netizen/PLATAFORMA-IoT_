# Delta de Especificación: Plataforma Streamlit

## ADDED Requirements

### Requirement: Telemetría simulada con fail-safe
La plataforma SHALL poder cargar 12 bovinos activos con telemetría relativa de 48 horas, incluyendo lecturas con `fix_valido=0` que no sustituyen la última coordenada válida.

#### Scenario: Simulación de GPS sin fix
- **WHEN** el simulador inserta una lectura con `fix_valido=0` y coordenadas inválidas
- **THEN** la lectura queda registrada con `fix_valido=0`
- **AND** la última ubicación vigente del animal continúa siendo la última coordenada válida

#### Scenario: Dashboard con resultados integrales
- **WHEN** se abre el dashboard Streamlit después de la simulación
- **THEN** hay 12 animales activos, trayectorias recientes y alertas de al menos tres tipos distintos
