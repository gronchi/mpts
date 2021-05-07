function CrioConfigFile(Trigger,Timer,Filename,IIGateShift,PlotOn); 
% creates config file for crio system from Times 
% Trigger is returned by TriggerMPTS.m
% Timer is returned by TimersMPTS.m
% IIGateShift - shift of IIGate triggers, us

if nargin<4; IIGateShift=0; end;
if nargin<5; PlotOn=0; end; 

fid=fopen(Filename,'wt');  
fprintf(fid,'Simmer_delay(1uS) = "%1.0f"\n',Timer.Simmer.Delay); 
fprintf(fid,'Burst_delay(1uS) = "%1.0f"\n',Trigger.Burst.Delay ); 
fprintf(fid,'Burst_number = "%1.0f"\n',Trigger.Burst.N);
fprintf(fid,'Burst_period(1uS) = "%1.0f"\n',Trigger.Burst.Period);
fprintf(fid,'Trigger_Enable_pulse(1uS) = "%1.0f"\n',Timer.Enable.Width);

fprintf(fid,'ADC_Enable_delay(1uS) = "%1.0f"\n',Trigger.ADC.Delay);
fprintf(fid,'ADC_Enable_pulse(1uS) = "%1.0f"\n',Trigger.ADC.Width);

fprintf(fid,'CMOS_plasma_delay(1uS) = "%1.0f"\n',Trigger.CMOSPlasma.Delay);
fprintf(fid,'CMOS_Plasma_number = "%1.0f"\n',Trigger.CMOSPlasma.N);
fprintf(fid,'CMOS_Plasma_period(1uS) = "%1.0f"\n', Trigger.CMOSPlasma.Period);
fprintf(fid,'CMOS_Plasma_pulse(1uS) = "%1.0f"\n',Trigger.CMOSPlasma.Width);

fprintf(fid,'CMOS_Laser_delay(0.1uS) = "%1.0f"\n',10*Trigger.CMOSLaser.Delay);
fprintf(fid,'CMOS_Laser_pulse(0.1uS) = "%1.0f"\n',10*Trigger.CMOSLaser.Width);

fprintf(fid,'II_Gate_Plasma_delay(0.1uS) = "%1.0f"\n',10*(Trigger.IIGatePlasma.Delay+IIGateShift));
fprintf(fid,'II_Gate_Plasma_number = "%1.0f"\n',Trigger.IIGatePlasma.N);
fprintf(fid,'II_Gate_Plasma_period(0.1uS) = "%1.0f"\n',10*Trigger.IIGatePlasma.Period);
fprintf(fid,'II_Gate_Plasma_pulse(0.1uS) = "%1.0f"\n',10*Trigger.IIGatePlasma.Width);
fprintf(fid,'II_Plasma_Delay_delay(0.1uS) = "%1.0f"\n',10*(Trigger.IIPlasmaRetard.Delay+IIGateShift));
fprintf(fid,'II_Plasma_Delay_pulse(0.1uS) = "%1.0f"\n',10*Trigger.IIPlasmaRetard.Width);

fprintf(fid,'II_Gate_Laser_delay(0.1uS) = "%1.0f"\n',10*(Trigger.IIGateLaser.Delay+IIGateShift));
fprintf(fid,'II_Gate_Laser_pulse(0.1uS) = "%1.0f"\n',10*Trigger.IIGateLaser.Width);

fprintf(fid,'II_Flash_Bool_delay(1uS) = "%1.0f"\n',Trigger.FlashBool.Delay);
fprintf(fid,'II_Flash_Bool_pulse(1uS) = "%1.0f"\n',Trigger.FlashBool.Width);

fprintf(fid,'Flash_delay(1uS) = "%1.0f"\n',Trigger.Flash.Delay);
fprintf(fid,'Flash_pulse(1uS) = "%1.0f"\n',Trigger.Flash.Width);

fprintf(fid,'Pockels_delay(1uS) = "%1.0f"\n',Trigger.Pockels.Retard);
fprintf(fid,'Pockels_number = "%1.0f"\n',Trigger.Pockels.N);
fprintf(fid,'Pockels_period(1uS) = "%1.0f"\n',Trigger.Pockels.Period);
fprintf(fid,'Pockels_pulse(1uS) = "%1.0f"\n',Trigger.Pockels.Width);
fprintf(fid,'CMOSLOn = "%1.0f"\n',Trigger.CMOSLaser.On);
fprintf(fid,'CMOSPOn = "%1.0f"\n',Trigger.CMOSPlasma.On);

fprintf(fid,'A1_SW_enable = "%1.0f"\n',Timer.Charge.On);
fprintf(fid,'A2_SW_enable = "%1.0f"\n',Timer.Simmer.On);
fprintf(fid,'A4_SW_enable = "1"\n');

fprintf(fid,'End_of_file = "empty"\n');
fprintf(fid,'=======================\n');
if Trigger.CMOSLaser.On&Trigger.CMOSPlasma.On
   fprintf(fid,'CMOSLaser Number = "%1.0f"\n',Trigger.Burst.N*Trigger.CMOSPlasma.N);
   fprintf(fid,'CMOSPlasma Number  = "%1.0f"\n',Trigger.Burst.N*Trigger.CMOSPlasma.N);
end; 
if Trigger.CMOSLaser.On&not(Trigger.CMOSPlasma.On)
   fprintf(fid,'CMOSLaser Number = "%1.0f"\n',2*Trigger.Burst.N*Trigger.CMOSPlasma.N);
end; 
if not(Trigger.CMOSLaser.On)&Trigger.CMOSPlasma.On
   fprintf(fid,'CMOSPlasma Number = "%1.0f"\n',2*Trigger.Burst.N*Trigger.CMOSPlasma.N);
end;

if not(Trigger.CMOSLaser.On)&not(Trigger.CMOSPlasma.On)
   fprintf(fid,'Both CMOS cameras Off\n'); 
end;


fclose(fid);

if PlotOn
disp(['Simmer_delay(1uS) = ', num2str(Timer.Simmer.Delay)]); 
disp(['Burst_delay(1uS) = ', num2str(Trigger.Burst.Delay )]); 
disp(['Burst_number = ', num2str(Trigger.Burst.N)]);
disp(['Burst_period(1uS) = ', num2str(Trigger.Burst.Period)]);
disp(['Trigger_Enable_pulse(1uS) = ', num2str(Timer.Enable.Width)]);

disp(['ADC_Enable_delay(1uS) = ', num2str(Trigger.ADC.Delay)]);
disp(['ADC_Enable_pulse(1uS) = ', num2str(Trigger.ADC.Width)]);

disp(['CMOS_plasma_delay(1uS) = ', num2str(Trigger.CMOSPlasma.Delay)]);
disp(['CMOS_Plasma_number = ', num2str(Trigger.CMOSPlasma.N)]);
disp(['CMOS_Plasma_period(1uS) = ', num2str( Trigger.CMOSPlasma.Period)]);
disp(['CMOS_Plasma_pulse(1uS) = ', num2str(Trigger.CMOSPlasma.Width)]);

disp(['CMOS_Laser_delay(0.1uS) = ', num2str(10*Trigger.CMOSLaser.Delay)]);
disp(['CMOS_Laser_pulse(0.1uS) = ', num2str(10*Trigger.CMOSLaser.Width)]);

disp(['II_Gate_Plasma_delay(0.1uS) = ', num2str(10*Trigger.IIGatePlasma.Delay)]);
disp(['II_Gate_Plasma_number = ', num2str(Trigger.IIGatePlasma.N)]);
disp(['II_Gate_Plasma_period(0.1uS) = ', num2str(10*Trigger.IIGatePlasma.Period)]);
disp(['II_Gate_Plasma_pulse(0.1uS) = ', num2str(10*Trigger.IIGatePlasma.Width)]);
disp(['II_Plasma_Delay_delay(0.1uS) = ', num2str(10*Trigger.IIPlasmaRetard.Delay)]);
disp(['II_Plasma_Delay_pulse(0.1uS) = ', num2str(10*Trigger.IIPlasmaRetard.Width)]);

disp(['II_Gate_Laser_delay(0.1uS) = ', num2str(10*Trigger.IIGateLaser.Delay)]);
disp(['II_Gate_Laser_pulse(0.1uS) = ', num2str(10*Trigger.IIGateLaser.Width)]);

disp(['II_Flash_Bool_delay(1uS) = ', num2str(Trigger.FlashBool.Delay)]);
disp(['II_Flash_Bool_pulse(1uS) = ', num2str(Trigger.FlashBool.Width)]);

disp(['Flash_delay(1uS) = ', num2str(Trigger.Flash.Delay)]);
disp(['Flash_pulse(1uS) = ', num2str(Trigger.Flash.Width)]);

disp(['Pockels_delay(1uS) = ', num2str(Trigger.Pockels.Retard)]);
disp(['Pockels_number = ', num2str(Trigger.Pockels.N)]);
disp(['Pockels_period(1uS) = ', num2str(Trigger.Pockels.Period)]);
disp(['Pockels_pulse(1uS) = ', num2str(Trigger.Pockels.Width)]);

    
end; 