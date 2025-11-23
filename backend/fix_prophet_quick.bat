@echo off
REM Quick Prophet fix using conda-forge

echo ========================================
echo Quick Prophet Fix (Recommended)
echo ========================================
echo.

call conda activate currency-intelligence

echo Uninstalling pip versions...
pip uninstall prophet pystan cmdstanpy -y

echo.
echo Installing Prophet from conda-forge (includes CmdStan)...
conda install -c conda-forge prophet -y

echo.
echo Installing compatible dependencies...
pip install numpy==1.24.3 --force-reinstall
pip install scikit-learn==1.3.2 --force-reinstall --no-build-isolation

echo.
echo ========================================
echo ✅ Prophet fix complete!
echo ========================================
echo.
echo Testing...
python -c "from prophet import Prophet; import pandas as pd; import numpy as np; df = pd.DataFrame({'ds': pd.date_range('2020-01-01', periods=100, freq='D'), 'y': np.random.randn(100).cumsum()}); m = Prophet(); m.fit(df); print('✅ Prophet is working perfectly!')"

echo.
pause


