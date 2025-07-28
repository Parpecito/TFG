# TFG: Comparativa de distintos frameworks especializados y lideres en de desarrollo de arquitecturas multiagentes para la resolución de casos de uso que se enmarcan en el sector financiero

## Descripción del proyecto
Este Trabajo de Fin de Grado (TFG) evalúa y compara dos frameworks de arquitecturas multiagente **Autogen** y **LangGraph** en su aplicabilidad dentro de este sector. A través de tres casos de uso prácticos, se analizan aspectos como:

- Rendimiento y escalabilidad  
- Trazabilidad y auditoría  
- Robustez y tolerancia a fallos  
- Facilidad de integración en entornos empresariales  

El objetivo es proporcionar una guía técnica y práctica que oriente a profesionales e instituciones financieras en la selección e implementación de soluciones multiagente basadas en modelos de lenguaje (LLMs) utilizando los frameworks más actuales.

## Casos de usos desarrollados
1. Análisis financiero de una empresa donde en Autogen utiliza MCP y LangGraph no utiliza MCP.
2. Sistema multiagente de análisis de noticias financieras
3. Sistema multiagente de análisis financiero utilizando tecnología MCP.

## Estructura del repositorio

```plaintext
TFG/
├── Caso de Uso 1 Autogen/
├── Caso de Uso 1 LangGraph/
├── Caso de Uso 2 Autogen/
├── Caso de Uso 2 LangGraph/
├── Caso de Uso 3 Autogen/
└── Caso de Uso 3 LangGraph/
```
## Requisitos para ejecutar
Cada caso de uso tendrá un archivo requierement.txt donde vendrá lo necesario para ejecuta el programa
Además, el usuario necesita tener las API KEY que hay en los .env

## Instalación y despliegue
### 1. Clonar el repositorio:
```bash
git clone https://github.com/Parpecito/TFG.git
cd TFG
```

### 2. Crear y activar el entorno virtual (Python)

#### En Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### En Windows (CMD):
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

#### En Windows (PowerShell):
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```


### 3. Configurar variables de entorno para la API de LLM y credenciales de base de datos.

### 4. Ejecutar cada caso de uso:
```bash
cd "Caso de Uso 1 Autogen"
python main.py
```

Repite el proceso para todos los casos de usos.

###  Notas adicionales 

- El proyecto requiere **Python 3.11.9**.

