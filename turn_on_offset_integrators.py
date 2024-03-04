from oei import *
# turn_on_offset_integrators.py; use this script to turn on offset integrators (or off) which may improve noise RMS. Note that this script should only be run after tuning the offsets to close to 8196 to ensure the offset integrators work properly.

def write_and_read(thing, CmdString, get_response=True):
    CmdByteList = []
    #print('Sending command: ', CmdString)
    for ch in CmdString:
        CmdByteList.append(ord(ch))

    CmdByteList.append(0x0d) # tack on CR
    for i in range((len(CmdByteList)+49)//50):
        thing.writef(0x90000000, CmdByteList[i*50:(i+1)*50])

    ResString = ""
    if get_response:
        more = 40
        #print(' ')
        #print('Response: ')
        while more > 0:
            ResByteList = thing.readf(0x90000000,50)
            for b in ResByteList[2:]:
                if b==255:
                    break
                elif b==1:
                    ResString += "[START]"
                elif b==2:
                    ResString += "[RESULT]"
                elif b==3:
                    ResString += "[END]"
                elif chr(b).isprintable:
                    more = 40
                    ResString = ResString + chr(b)
            sleep(0.005)
            more -= 1
        ResString = ResString + chr(0)
        #print(ResString)

def main():
    turn_on = True
    IP_endpoints=[100]
    AFEs = [0,1,2,3,4]
    for i in IP_endpoints:
        for AFE in AFEs:
            if turn_on:
                # configure LNA
                write_and_read(thing, 'WR AFE '+ str(int(AFE)) + ' REG 52 V 16896', get_response=True)
                # configure PGA
                write_and_read(thing, 'WR AFE '+ str(int(AFE)) + ' REG 51 V 0', get_response=True)
                # change to 10MHz low pass filter
                #write_and_read(thing, 'WR AFE '+ str(int(AFE)) + ' REG 51 V 8', get_response=True)
            else:
                write_and_read(thing, 'WR AFE '+ str(int(AFE)) + ' REG 52 V 21056', get_response=True)
                write_and_read(thing, 'WR AFE '+ str(int(AFE)) + ' REG 51 V 16', get_response=True)
