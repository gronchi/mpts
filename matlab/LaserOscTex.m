function PulseEn=LaserOscTex(FilePC,FileChDir,FileChRet,EnDir,EnRet,CorrectOn,PlotOn); 
% Laser pulse power and energy from Textronic scope 
% PC - channel with Pockels cell pulses, [time, Volt]
% ChDir,ChRet  - Laser signals from direct and return laser beams,[time, Volt]
% EnDir, EnRet - Ophir measures of the direct and return energies
% CorrectOn - correct zero lines of laser signals so that to exlude 
%             free oscillation energy 
% PC, ChDir, ChRet are readout from ifs files: 
% ChDir = isfread ('*.isf');
% LaserOscTex('..\data\20171207\scope\12_CH1.isf', '..\data\20171207\scope\12_CH3.isf', '..\data\20171207\scope\12_CH2.isf', 0.674, 0.401, 0, 1)

if nargin<6; CorrectOn=0; end;
if nargin<7; PlotOn=0; end; 

PassN=14; % number of passes in MPS

PC = isfread (FilePC);
ChDir = isfread (FileChDir);
ChRet = isfread (FileChRet);
N=length(PC); 

% Indexing On and Off intervals of PC pulses: 
Mean=mean(PC.y); Std=std(PC.y);
LevelPC=mean(PC.y(abs(PC.y-Mean)<Std)); 
StdLevelPC=std(PC.y(abs(PC.y-Mean)<Std));
PC.z=(PC.y-LevelPC)/max(PC.y-LevelPC);
PC.x=PC.x*1000;
Tact=mean(diff(PC.x));  % ms
PCOnInd=find(PC.z>3*StdLevelPC); PCOnInd=[1;PCOnInd];
DiffPCOnInd=diff(PCOnInd); 
PCEndInd=PCOnInd(DiffPCOnInd>1); 
PCEndInd(1)=[]; 
PCEndInd(end+1)=find(PC.z>3*StdLevelPC,1,'last');
PCOnInd(1)=[]; 
PCStartInd=PCOnInd(DiffPCOnInd>1); 
PCStartN=length(PCStartInd);
PCEndN=length(PCEndInd);
if PCEndN==PCStartN; PCN=PCEndN; end; 

LevelDir=mean(ChDir.y(1:PCStartInd(1))); ChDir.x=ChDir.x*1000;
ChDir.Power=EnDir*(LevelDir-ChDir.y)/sum(LevelDir-ChDir.y)/Tact/1000;    % MW
StdPowerDir=std(ChDir.Power(1:PCStartInd(1)));
LevelRet=mean(ChRet.y(1:PCStartInd(1))); ChRet.x=ChRet.x*1000;
ChRet.Power=EnRet*(LevelRet-ChRet.y)/sum(LevelRet-ChRet.y)/Tact/1000;    % MW
StdPowerRet=std(ChRet.Power(1:PCStartInd(1)));

PulseEn=zeros(PCN,5);
BkgPower=zeros(PCN,2);
disp(PCStartInd')
disp(PCEndInd')
for i=1:PCN
    [Max,maxInd]=max(ChDir.Power(PCStartInd(i):PCEndInd(i))); 
    maxInd=maxInd+PCStartInd(i)-1;
    PulseEn(i,1)=PC.x(maxInd); 
    
    Ind1=PCStartInd(i)-1+find(ChDir.Power(PCStartInd(i):maxInd)>2*StdPowerDir,1,'first');
    Ind2=maxInd-1+find(ChDir.Power(maxInd:PCEndInd(i))<2*StdPowerDir,1,'first');
    if isempty(Ind2); Ind2=PCEndInd(i); end; 
    IndN=length(Ind1:Ind2);
    PulseEn(i,2)=sum(ChDir.Power(Ind1:Ind2))*Tact*1000;
    BkgPower(i,1)=mean(ChDir.Power([PCStartInd(i):Ind1-1,Ind2:PCEndInd(i)]));
    PulseEn(i,2)=PulseEn(i,2)-BkgPower(i,1)*IndN*Tact*1000;
    % Pulse width, us:
    PulseEn(i,5)=PulseEn(i,2)/Max; 
    
    Ind1=PCStartInd(i)-1+find(ChRet.Power(PCStartInd(i):maxInd)>2*StdPowerRet,1,'first');
    Ind2=maxInd-1+find(ChRet.Power(maxInd:PCEndInd(i))<2*StdPowerRet,1,'first');
    if isempty(Ind2); Ind2=PCEndInd(i); end; 
    IndN=length(Ind1:Ind2);
    PulseEn(i,3)=sum(ChRet.Power(Ind1:Ind2))*Tact*1000;
    BkgPower(i,2)=mean(ChRet.Power([PCStartInd(i):Ind1-1,Ind2:PCEndInd(i)]));
    PulseEn(i,3)=PulseEn(i,3)-BkgPower(i,2)*IndN*Tact*1000;
    % Delay of the pulse peak from PC start, us: 
    PulseEn(i,4)=(maxInd-PCStartInd(i))*Tact*1000; 
    
    
    
end;

FreeEn=zeros(PCN-1,3);
for i=1:PCN-1
    FreeEn(i,1)=mean(PC.x(PCEndInd(i):PCStartInd(i+1))); 
    FreeEn(i,2)=sum(ChDir.Power((PCEndInd(i):PCStartInd(i+1))))*Tact*1000;
    FreeEn(i,3)=sum(ChRet.Power((PCEndInd(i):PCStartInd(i+1))))*Tact*1000;
end;

% if CorrectOn
%    PulseEn(1,2)=PulseEn(1,2)+FreeEn(1,2)/2; PulseEn(end,2)=PulseEn(end,2)+FreeEn(end,2)/2;
%    for i=2:PCN-1
%       PulseEn(i,2)=PulseEn(i,2)+(FreeEn(i-1,2)+FreeEn(i,2))/2; 
%    end; 
%    PulseEn(1,3)=PulseEn(1,3)+FreeEn(1,3)/2; PulseEn(end,3)=PulseEn(end,3)+FreeEn(end,3)/2;
%    for i=2:PCN-1
%       PulseEn(i,3)=PulseEn(i,3)+(FreeEn(i-1,3)+FreeEn(i,3))/2; 
%    end;    
% end; 

% Portions of return energy: 
PulseEn(:,6)=PulseEn(:,3)./PulseEn(:,2); 
q=PulseEn(:,6).^(1/PassN); 
K=(1-q.^PassN)./(1-q);
K(q>=1)=PassN;
% Total probing energy in MPS:
PulseEn(:,7)=PulseEn(:,2).*K;

if PlotOn
figure; 
subplot(2,1,1); hold on;
plot(PC.x,PC.z,'k');    % PC pulses
plot(ChDir.x,ChDir.Power,'r','Linewidth',2);    % Pulse power, direct
plot(ChRet.x,ChRet.Power,'b','Linewidth',2);    % Pulse power, return
plot(PulseEn(:,1),PulseEn(:,2),'ro','Linewidth',2);  % Pulse energy, direct
plot(PulseEn(:,1),PulseEn(:,3),'b*','Linewidth',2);  % Pulse energy, return 
plot(PulseEn(:,1),PulseEn(:,7),'g*','Linewidth',2); % Total probing energy in MPS
plot(FreeEn(:,1),FreeEn(:,2),'mo','Linewidth',2); % Free energy, direct
plot(FreeEn(:,1),FreeEn(:,3),'c*','Linewidth',2); % Free energy, return
plot(PulseEn(:,1),PulseEn(:,5),'g^','Linewidth',2);    % Pulse width
grid on; xlabel('t,ms'); ylabel('MW, J'); 

subplot(2,1,2); hold on;
plot(PulseEn(:,1),10*PulseEn(:,6),'k^','Linewidth',2); % return fraction 
plot(PulseEn(:,1),PulseEn(:,4),'ro','Linewidth',2);    % Delay of the pulse peak 
% plot(PulseEn(:,1),PulseEn(:,5),'b*','Linewidth',2);    % Pulse width
grid on; xlabel('t,ms'); ylabel('%/10, \mus'); 


end;

