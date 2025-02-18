# This script clears any gurobi license info from the devcontainer
if [ -f /opt/gurobi/gurobi1101/gurobi.lic ]; then
    rm /opt/gurobi/gurobi1101/gurobi.lic
fi
if [ -f /home/vscode/gurobi.lic ]; then
    rm /home/vscode/gurobi.lic
fi
