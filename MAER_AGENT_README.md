MAER Agent setup

Pasos recomendados:

1. Hacer ejecutable el script:

   chmod +x maer_agent_setup.sh

2. Ejecutarlo para crear el archivo del agente y lanzar lint/tests:

   ./maer_agent_setup.sh

3. Si el script falla en instalar dependencias, instala manualmente:

   npm install
   python -m pip install -r requirements.txt

4. Pega la salida completa del script en el chat para que el agente analice fallos y proponga parches.

