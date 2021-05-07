function [ data, settings ] = mpts_readshot( shot, experiment, withsettings  )
% [ Ys, Ts, YLs, TLs, ADCs ] = tcabr_readshot( DISP, QUAIS, Dt, SAVEFILE )
%
% To get several signals of one shot in a single structure.
%
%  "Ys" and "Ts" are the structures that contain the measured values and
%     the correspondent times of the "signals" in shot "DISP" at the 
%     time interval "Dt". "YLs" and "TLs" are the corresponding labels and 
%     "ADCs" gives the names of the ADCs.
%

list_signals = ['\\Phantom1Signal', '\\Phantom2Signal', '\\Phantom2Signal']
if ~exist('experiment','var') || isempty(experiment)
    experiment = 'mpts'
    return
end
if ~exist('withsettings','var')||isempty(withsettings)
    withsettings = 0;
end

mdsconnect('130.183.56.68:8000');
mdsopen(experiment, shot );
try
    data.shot = shot
    data.camera1 = mdsvalue('\Phantom1Signal');
    data.camera2 = mdsvalue('\Phantom2Signal');
    data.adc.y(2,:) = mdsvalue('\ADCCH1Signal')
    data.adc.y(1,:) = mdsvalue('\ADCCH1Signal')
    data.adc.t = mdsvalue('dim_of(\ScopeCH1Signal)')
    data.scope.y(4,:) = mdsvalue('\ScopeCH4Signal')
    data.scope.y(3,:) = mdsvalue('\ScopeCH3Signal')
    data.scope.y(2,:) = mdsvalue('\ScopeCH2Signal')
    data.scope.y(1,:) = mdsvalue('\ScopeCH1Signal')
    data.scope.t = mdsvalue('dim_of(\ScopeCH1Signal)')
    if withsettings
        Timer.Simmer.Delay = mdsvalue('\A2_Delay'); 
        Trigger.Burst.Delay = mdsvalue('\A4_Delay'); 
        Trigger.Burst.N = mdsvalue('\A4_Number');
        Trigger.Burst.Period = mdsvalue('\A4_Period');
        Timer.Enable.Width = mdsvalue('\A5_Pulse');
        Timer.Enable.Delay = mdsvalue('\B1_Delay');
        Timer.Enable.Width = mdsvalue('\B1_Pulse');
        Trigger.CMOSPlasma.Delay = mdsvalue('\B2_Delay');
        Trigger.CMOSPlasma.N = mdsvalue('\B2_Number');
        Trigger.CMOSPlasma.Period = mdsvalue('\B2_Period');
        Trigger.CMOSPlasma.Width = mdsvalue('\B2_Pulse');
        Trigger.CMOSLaser.Delay = mdsvalue('\B4_Delay') / 10;
        Trigger.CMOSLaser.Width = mdsvalue('\B4_Pulse') / 10;
        Trigger.IIGatePlasma.Delay = mdsvalue('\B5_Delay') / 10;
        Trigger.IIGatePlasma.N = mdsvalue('\B5_Number');
        Trigger.IIGatePlasma.Period = mdsvalue('\B5_Period') / 10;
        Trigger.IIGatePlasma.Width = mdsvalue('\B5_Pulse') / 10;
        Trigger.IIPlasmaRetard.Delay = mdsvalue('\B6_Delay') / 10;
        Trigger.IIPlasmaRetard.Width  = mdsvalue('\B6_Pulse')/ 10;
        Trigger.IIGateLaser.Delay = mdsvalue('\B7_Delay') / 10;
        Trigger.IIGateLaser.Width = mdsvalue('\B7_Pulse')/ 10
        Trigger.FlashBool.Delay = mdsvalue('\B8_Delay');
        Trigger.FlashBool.Width = mdsvalue('\B8_Pulse');
        Trigger.Flash.Delay = mdsvalue('\B9_Delay');
        Trigger.Flash.Width = mdsvalue('\B9_Pulse');
        Trigger.Pockels.Retard = mdsvalue('\B12_Delay');
        Trigger.Pockels.N = mdsvalue('\B12_Number');
        Trigger.Pockels.Period = mdsvalue('\B12_Period');
        Trigger.Pockels.Width = mdsvalue('\B12_Pulse');

        settings.Trigger = Trigger
        settings.Timer = Timer

        settings.LaserPS.MainVoltage = mdsvalue('\MainVoltage');
        settings.LaserPS.Enabled = mdsvalue('\LaserPSEnabled')
        settings.LaserPS.SerialPort = mdsvalue('\LaserPSSerialPort')
        settings.LaserPS.MainVoltage = mdsvalue('\LaserPSMainVoltage')
        settings.LaserPS.Aux1Voltage = mdsvalue('\LaserPSAux1Voltage')
        settings.LaserPS.Aux2Voltage = mdsvalue('\LaserPSAux2Voltage')
        settings.LaserPS.Aux3Voltage = mdsvalue('\LaserPSAux3Voltage')
        settings.LaserPS.AuxDelay = mdsvalue('\LaserPSAuxDelay')
        settings.LaserPS.SimmerDelay = mdsvalue('\LaserPSSimmerDelay')
        settings.LaserPS.BurstNumber = mdsvalue('\LaserPSBurstNumber')
        settings.LaserPS.BurstSep = mdsvalue('\LaserPSBurstSeperation')
        settings.LaserPS.ResMainV = mdsvalue('\LaserPSResMainVoltage')
        settings.LaserPS.ResAuxV = mdsvalue('\LaserPSResAuxVoltage')
        settings.LaserPS.MaxBurstN = mdsvalue('\LaserPSMaxBurstNumber')
        settings.LaserPS.MaxBurstDur = mdsvalue('\LaserPSMaxBurstDuration')
        settings.LaserPS.MaxExpEnerg = mdsvalue('\LaserPSMaxExpEnergy')
        settings.LaserPS.AccurCharge = mdsvalue('\LaserPSAccurCharge')
        settings.LaserPS.MaxDelFlash = mdsvalue('\LaserMaxDelayFlash')
        settings.LaserPS.TrigSimmer = mdsvalue('\LaserPSTriggerSimmer')
        settings.LaserPS.SignalReady = mdsvalue('\LaserPSSignalReady')
        settings.LaserPS.BankMode = mdsvalue('\LaserPSBankMode')
        settings.LaserCooling.MinIntTemp = mdsvalue('\LaserCoolingMinIntTemp')
        settings.LaserCooling.MaxIntTemp = mdsvalue('\LaserCoolingMaxIntTemp')
        settings.LaserCooling.OptIntFlow = mdsvalue('\LaserCoolingOptIntFlow')
        settings.LaserCooling.OptExtFlow = mdsvalue('\LaserCoolingOptExtFlow')
        settings.LaserCooling.MinExtFlow = mdsvalue('\LaserCoolingMinExtFlow')
        settings.LaserCooling.ModeBanks = mdsvalue('\LaserPSModeBanks')

        settings.Ophir.Description = mdsvalue('\OphirDescription')
        settings.Ophir.Enabled = mdsvalue('\OphirEnabled')
        settings.Ophir.SerialPort = mdsvalue('\OphirSerialPort')
        settings.Ophir.Coef1 = mdsvalue('\OphirCoef1')
        settings.Ophir.Coef2 = mdsvalue('\OphirCoef2')
        settings.Ophir.Head1 = mdsvalue('\OphirHead1')
        settings.Ophir.Head2 = mdsvalue('\OphirHead2')
        %settings.Ophir.EnergyDirect = mdsvalue('OphirEnergyDirect')
        %settings.Ophir.EnergyReturn = mdsvalue('OphirEnergyReturn')
    end
catch
    disp( 'Error reading SHOT %d', shots(i)) %#ok<WNTAG>
end
mdsdisconnect();
return

end

% -------------------------------------------------
function ALL = addshotfield(ALL, NEW)
if isempty( ALL )
    ALL = NEW;
else
    FIELDs = fieldnames( NEW );
    N = length( ALL );
    for qF = 1 : length( FIELDs )
        ALL(N+1).(FIELDs{qF}) = NEW.(FIELDs{qF});
    end
end
% -------------------------------------------------
function savefilefields( DISP, SAVEFILE, FIELD_ATU, Ys, Ts, YLs, TLs, ADCs )
% FILE_NAME_ATU = sprintf('tcabr_%d_%s.mat', DISP, FIELD_ATU );
FILE_NAME_ATU = sprintf('tcabr_data_%d_%s.mat', DISP, FIELD_ATU );
if SAVEFILE>=2 || ~exist( FILE_NAME_ATU, 'file' )
    Ys2.(FIELD_ATU) = Ys.(FIELD_ATU); Ys2.shot = Ys.shot; Ys = Ys2; %#ok<NASGU>
    YLs2.(FIELD_ATU) = YLs.(FIELD_ATU); YLs2.shot = YLs.shot; YLs = YLs2; %#ok<NASGU>
    Ts2.(FIELD_ATU ) = Ts.(FIELD_ATU ); Ts = Ts2; %#ok<NASGU>
    TLs2.(FIELD_ATU ) = TLs.(FIELD_ATU ); TLs = TLs2; %#ok<NASGU>
    ADCs2.(FIELD_ATU ) = ADCs.(FIELD_ATU ); ADCs = ADCs2; %#ok<NASGU>
    save( FILE_NAME_ATU, 'Ys', 'Ts', 'YLs', 'TLs', 'ADCs' )
    disp( sprintf( 'The %s file was saved', FILE_NAME_ATU ) )
end