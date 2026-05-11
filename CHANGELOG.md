# Release v0.7.1: Ejecutables Windows & Tags

## 🇪🇸 Español

### 🚀 Nuevas Funcionalidades
* **Soporte para ejecutables nativos de Windows:** Kharōn ahora soporta la ejecución de archivos `.exe`, `.bat` y `.cmd` como scripts orquestados. Los `.exe` se ejecutan directamente, mientras que `.bat`/`.cmd` se ejecutan a través de `cmd.exe /c`. Esto permite orquestar procesos batch legacy y herramientas compiladas sin modificaciones.
* **Selector de intérprete ampliado:** El formulario de "Nuevo Script" ahora incluye las opciones Ejecutable (.exe), Batch (.bat), CMD (.cmd) y PowerShell (.ps1) además de Bash, Python y Shell.

### 🐛 Correcciones
* **Tags visibles en Procesos:** Los tags personalizados creados al registrar un script (ej: `etl`, `diarios`, `producción`) ahora se muestran como pastillas violeta en la tarjeta de cada proceso en la página Procesos. Anteriormente se guardaban correctamente pero no se renderizaban en la interfaz.

---

## 🇺🇸 English

### 🚀 New Features
* **Windows native executable support:** Kharōn now supports executing `.exe`, `.bat`, and `.cmd` files as orchestrated scripts. `.exe` files run directly, while `.bat`/`.cmd` are executed via `cmd.exe /c`. This enables orchestrating legacy batch processes and compiled tools without modifications.
* **Expanded interpreter selector:** The "New Script" form now includes Executable (.exe), Batch (.bat), CMD (.cmd), and PowerShell (.ps1) options in addition to Bash, Python, and Shell.

### 🐛 Fixes
* **Tags visible in Processes:** Custom tags created when registering a script (e.g., `etl`, `daily`, `production`) now display as purple pills on each process card in the Processes page. Previously they were saved correctly but not rendered in the UI.

---

# Release v0.7.0: Native Windows Daemon & PostgreSQL

## 🇪🇸 Español

### 🚀 Nuevas Funcionalidades
* **Instalación Nativa en Windows (sin Nested Virtualization):** Ahora Kharōn soporta instalación en modo "fall-back" a través de WSL1, ideal para entornos de servidores o máquinas virtuales (ej. QEMU, VirtualBox, AWS) donde los contenedores y WSL2 fallan.
* **Motor PostgreSQL Integrado:** Se reemplazó el SQLite por defecto con PostgreSQL nativo dentro de WSL. Esto soluciona problemas de latencia y errores de concurrencia (`locking protocol`) característicos del sistema de archivos de Windows, blindando la estabilidad de Apache Airflow.
* **Ejecución como Demonio (Segundo Plano):** Nuevas herramientas (`start_daemon.ps1` y `stop_daemon.ps1`) permiten lanzar el ecosistema completo (DB + Airflow + Streamlit) de forma silenciosa e invisible.
* **Servicio de Arranque Automático:** Se integró el instalador `install_service.ps1` para programar Kharōn como una tarea crítica del sistema (Task Scheduler). Ahora arranca automáticamente al encender el equipo con los máximos privilegios, sin siquiera requerir que el usuario inicie sesión.

### 🧹 Mejoras y Correcciones
* **Limpieza Absoluta del Tablero:** Se deshabilitó explícitamente la inyección de los +40 DAGs de ejemplo (tutoriales) de Apache Airflow (`load_examples=False`). El ambiente inicia impecable.
* **Autenticación Sincronizada:** Streamlit ahora intercepta y lee dinámicamente el archivo de contraseñas generado al vuelo por Airflow, evitando errores 401 entre el frontend y la API.
* **Documentación Actualizada:** El archivo `README.md` refleja todo el troubleshooting paso a paso para la nueva arquitectura.

---

## 🇺🇸 English

### 🚀 New Features
* **Native Windows Installation (No Nested Virtualization):** Kharōn now supports "fall-back" installation via WSL1, ideal for server environments or virtual machines (e.g., QEMU, VirtualBox, AWS) where containers and WSL2 fail.
* **Integrated PostgreSQL Engine:** Replaced the default SQLite with native PostgreSQL within WSL. This resolves latency and concurrency issues (`locking protocol`) characteristic of the Windows filesystem, ensuring Apache Airflow's stability.
* **Daemon Execution (Background):** New tools (`start_daemon.ps1` and `stop_daemon.ps1`) allow launching the full ecosystem (DB + Airflow + Streamlit) silently and invisibly.
* **Automatic Startup Service:** Integrated the `install_service.ps1` installer to schedule Kharōn as a critical system task (Task Scheduler). It now starts automatically upon system boot with maximum privileges, without even requiring user login.

### 🧹 Improvements & Fixes
* **Absolute Dashboard Cleanup:** Explicitly disabled the injection of 40+ example DAGs (tutorials) from Apache Airflow (`load_examples=False`). The environment starts fresh.
* **Synchronized Authentication:** Streamlit now intercepts and dynamically reads the password file created on the fly by Airflow, preventing 401 sync errors between the frontend and API.
* **Updated Documentation:** The `README.md` file now includes a step-by-step troubleshooting guide for the WSL1 architecture.

---

## 🛠 What's Changed
* style: apply Ākāśa aesthetic to Kharōn webapp by @hbuddenberg in https://github.com/Arkh-Ur/kharon/pull/1
* docs: container deploy guide — step-by-step, beginner friendly by @hbuddenberg in https://github.com/Arkh-Ur/kharon/pull/2

## ✨ New Contributors
* @hbuddenberg made their first contribution in https://github.com/Arkh-Ur/kharon/pull/1
