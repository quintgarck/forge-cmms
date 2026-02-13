# Script para organizar archivos de documentación de ForgeDB

# Mover archivos de presupuesto
Move-Item -Path "presupuesto_inversion_proyecto.md" -Destination "presupuesto\"
Move-Item -Path "desglose_costos_recurso_humano.md" -Destination "presupuesto\"

# Mover archivos de planificación
Move-Item -Path "plan_seguimiento_detallado.md" -Destination "planificacion\"

# Mover archivos de reportes
Move-Item -Path "actualizacion_progreso_tarea1.md" -Destination "reportes\"
Move-Item -Path "actualizacion_progreso_tarea2.md" -Destination "reportes\"
Move-Item -Path "actualizacion_progreso_tarea3.md" -Destination "reportes\"
Move-Item -Path "verificacion_estado_tarea3.md" -Destination "reportes\"
Move-Item -Path "verificacion_final_proyecto_completo.md" -Destination "reportes\"

# Mover archivos de guía
Move-Item -Path "guia_desarrollo.md" -Destination "guia\"
Move-Item -Path "especificaciones_tecnicas.md" -Destination "guia\"

# Mover archivos principales que quedan
Move-Item -Path "README_proyecto_forgedb.md" -Destination "control\"
Move-Item -Path "estado_actual_proyecto.md" -Destination "control\"
Move-Item -Path "estado_real_verificado_proyecto.md" -Destination "control\"

# Mover archivos de resumen
Move-Item -Path "resumen_completo_proyecto_forgedb.md" -Destination "planificacion\"
Move-Item -Path "resumen_ejecutivo_plan_detallado.md" -Destination "planificacion\"
Move-Item -Path "resumen_ejecutivo_sistema_completo.md" -Destination "planificacion\"

# Mover decisiones y verificaciones
Move-Item -Path "decision_frontend_django_confirmada.md" -Destination "control\"