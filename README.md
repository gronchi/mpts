# MPTS Control and Acquisition
mpts is the software for control and data aquisition of the Multipass Thomson Scattering diagnostic in the Asdex Upgrade tokamak.

### Highlights
- Simple to use and resource efficient
- Written in Python 3 using QT5 for the user interface

 
### Python environment
Assuming you have Python >=3.X installed, the following additional modules are required (can be installed with "pip").
- pip install pyserial
- pip install pyqt5
- pip install mdsplus


### QT Creator
QT Creator (including QT Designer for UI design) can be downloaded [here](https://www.qt.io/download-open-source/).
You need to convert the mainwindow.ui to mainwindow.py (because of PyQt5). This is taken care of my executing pyinstaller-build.bat

NOTE: It is used strictly for editing the ui/mainwindow.ui file directly. It is not necessary to create a QT Project.


