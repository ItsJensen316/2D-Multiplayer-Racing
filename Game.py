import pygame
import math
pygame.init()
def end():
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            pygame.quit()
            
def direction(x,y,speed,angle):
    angle = math.radians(angle)
    new_x = x + (speed*math.cos(angle))
    new_y = y + (speed*math.sin(angle))
    return new_x, new_y

def hitbox(x,y,ang11):
    angrad1=math.radians(ang11-20)
    angrad2=math.radians(ang11+20)
    angrad3=math.radians(ang11-160)
    angrad4=math.radians(ang11+160)
    xline11 = x + math.cos(angrad1) * 30
    yline11 = y + math.sin(angrad1) * 30
    xline12 = x + math.cos(angrad2) * 30
    yline12 = y + math.sin(angrad2) * 30
    xline13 = x + math.cos(angrad3) * 30
    yline13 = y + math.sin(angrad3) * 30
    xline14 = x + math.cos(angrad4) * 30
    yline14 = y + math.sin(angrad4) * 30
    return xline11,yline11,xline12,yline12,xline13,yline13,xline14,yline14

fps=100
x=1132
y=720
x2=1130
y2=752
h=15
w=15
n=0
n2=0
cond=False
cond2=False
check=False
check1=False
check12=False
check2=False
freeze=False
freeze2=False
point=0
point2=0
ang1=0 #Initial angle of 1st car
ang11=180
ang2=0 #Initial angle of 2nd car
ang21=180
fpsclock=pygame.time.Clock()
screen=pygame.display.set_mode((1500,800))
pygame.display.set_caption("First Game - Updated")
track=pygame.image.load("track1.png")
arrow=pygame.image.load("arrow.png")
start=pygame.image.load("start.png")
start2=pygame.image.load("start2.png")
start3=pygame.image.load("start3.png")
show=True
round=int(input("Enter number of rounds: "))
while(show==True):
    mx,my=pygame.mouse.get_pos()
    ev=pygame.event.get()
    screen.blit(start,(0,0))
    if(950>mx>555 and 645>my>515):
        screen.blit(start3,(0,0))
        for event in ev:
            if event.type == pygame.MOUSEBUTTONUP:
                for i in range(0,100):
                    screen.blit(start2,(0,0))
                    pygame.display.update()
                for i in range(0,100):
                    screen.blit(start,(0,0))
                    pygame.display.update()
                show=False
    pygame.display.update()
    fpsclock.tick(fps)
        

car1=pygame.image.load("car1.png")
car11=pygame.image.load("car1.1.png")
car12=pygame.image.load("car1.2.png")
car2=pygame.image.load("car2.png")
car22=pygame.image.load("car2.2.png")
    
speed1=0
speed2=0
run=True
while (run==True):
    screen.blit(track,(0,0))
    screen.blit(arrow,(1020,570))
    '''pygame.draw.rect(screen,(255,0,0),(0,0,1500,800),50) #Outer rectangle
    pygame.draw.rect(screen,(255,0,0),(150,150,1200,500),20) #Inner rectangle'''
    pygame.draw.rect(screen,(250,250,250),(1085,702,15,70),5) #Start/Finish point
    #pygame.draw.rect(screen,(150,150,150),(54,500,85,15),5) #Invisible Checkpoint
    end()

    ###################PLAYER 1######################
    rotate1=pygame.transform.rotate(car1,ang1)
    rotate_rect=rotate1.get_rect(center=car1.get_rect(center=(x,y)).center)
    screen.blit(rotate1,rotate_rect)
    kinput=pygame.key.get_pressed()
    if(freeze==True):
        freeze=True
    else:
        #Car inputs
        if(kinput[pygame.K_RIGHT] and speed1!=0):
            if(speed1>0):
                ang1-=1
                ang11+=1
            else:
                ang1+=1
                ang11-=1
            ang1=ang1%360
        elif(kinput[pygame.K_LEFT] and speed1!=0):
            if(speed1>0):
                ang1+=1
                ang11-=1
            else:
                ang1-=1
                ang11+=1
            ang1=ang1%360
            
        #Car Physics
        if (kinput[pygame.K_UP]):
            speed1+=0.02
        else:
            if(speed1>0):
                speed1-=0.01
        if (kinput[pygame.K_DOWN]):
            speed1-=0.02
        else:
            if(speed1<0):
                speed1+=0.01
        x,y=direction(x,y,speed1,ang11)
        xline11,yline11,xline12,yline12,xline13,yline13,xline14,yline14=hitbox(x,y,ang11) #hitbox
        speed1=float(format(speed1,".2f"))
        #print(screen.get_at((int(xline11), int(yline11))))

    #Boundaries (Player-1)
    if(screen.get_at((int(xline11), int(yline11))) == (255,255,255,255) and freeze==False):
        if(360>=ang1>315 or 45>=ang1>0):
            x=x+3
            y=y-3
        elif(315>=ang1>225):
            x=x+3
            y=y+3
        elif(225>=ang1>135):
            x=x-3
            y=y+3
        elif(135>=ang1>45):
            x=x-3
            y=y-3
        cond=True
    if(screen.get_at((int(xline12), int(yline12))) == (255,255,255,255) and freeze==False):
        if(360>=ang1>315 or 45>=ang1>0):
            x=x+3
            y=y+3
        elif(315>=ang1>225):
            x=x-3
            y=y+3
        elif(225>=ang1>135):
            x=x-3
            y=y-3
        elif(135>=ang1>45):
            x=x+3
            y=y-3
        cond=True
    if(screen.get_at((int(xline13), int(yline13))) == (255,255,255,255) and freeze==False):
        if(360>=ang1>315 or 45>=ang1>0):
            x=x-3
            y=y-3
        elif(315>=ang1>225):
            x=x+3
            y=y-3
        elif(225>=ang1>135):
            x=x+3
            y=y+3
        elif(135>=ang1>45):
            x=x-3
            y=y+3
        cond=True
    if(screen.get_at((int(xline14), int(yline14))) == (255,255,255,255) and freeze==False):
        if(360>=ang1>315 or 45>=ang1>0):
            x=x-3
            y=y+3
        elif(315>=ang1>225):
            x=x-3
            y=y-3
        elif(225>=ang1>135):
            x=x+3
            y=y-3
        elif(135>=ang1>45):
            x=x+3
            y=y+3
        cond=True
    #pygame.draw.rect(screen,(255,255,255),pygame.Rect(x-23,y-10,30,20))
            
    if(cond==True):
        n=100
        speed1=0
        cond=False
        freeze=True
    if(n>0):
        if(n>75 or 50>n>25):
            rotate11=pygame.transform.rotate(car11,ang1)
            rotate_rect=rotate11.get_rect(center=car11.get_rect(center=(x,y)).center)
            screen.blit(rotate11,rotate_rect)
        else:
            rotate12=pygame.transform.rotate(car12,ang1)
            rotate_rect=rotate12.get_rect(center=car12.get_rect(center=(x,y)).center)
            screen.blit(rotate12,rotate_rect)
        n=n-1
    elif(n==0):
        freeze=False
        
    #Start/Finish point
    if(140>x>54 and 515>y>500):
        check1=True
    if(x>1000 and 100>y>30 and check1==True):
        check1=False
        check=True
    if(1100<x<1125 and 772>y>702 and check==True):
        point+=1
        check=False


    
    ###################PLAYER 2######################
    
    rotate2=pygame.transform.rotate(car2,ang2)
    rotate_rect2=rotate2.get_rect(center=car2.get_rect(center=(x2,y2)).center)
    screen.blit(rotate2,rotate_rect2)
    kinput2=pygame.key.get_pressed()
    if(freeze2==True):
        freeze2=True
    else:
        #Car inputs
        if(kinput2[pygame.K_d] and speed2!=0):
            if(speed2>0):
                ang2-=1
                ang21+=1
            else:
                ang2+=1
                ang21-=1
            ang2=ang2%360
        elif(kinput2[pygame.K_a] and speed2!=0):
            if(speed2>0):
                ang2+=1
                ang21-=1
            else:
                ang2-=1
                ang21+=1
            ang2=ang2%360
            
        #Car Physics
        if (kinput2[pygame.K_w]):
            speed2+=0.02
        else:
            if(speed2>0):
                speed2-=0.01
        if (kinput2[pygame.K_s]):
            speed2-=0.02
        else:
            if(speed2<0):
                speed2+=0.01
        x2,y2=direction(x2,y2,speed2,ang21)
        xline21,yline21,xline22,yline22,xline23,yline23,xline24,yline24=hitbox(x2,y2,ang21) #hitbox
        speed2=float(format(speed2,".2f"))
        '''pygame.draw.line(screen,(250,250,250),(x2,y2),(xline21,yline21),5)
        pygame.draw.line(screen,(250,250,250),(x2,y2),(xline22,yline22),5)
        pygame.draw.line(screen,(250,250,250),(x2,y2),(xline23,yline23),5)
        pygame.draw.line(screen,(250,250,250),(x2,y2),(xline24,yline24),5)'''

    #Boundaries (Player-2)
    if(screen.get_at((int(xline21), int(yline21))) == (255,255,255,255) and freeze2==False):
        if(360>=ang2>315 or 45>=ang2>0):
            x2=x2+3
            y2=y2-3
        elif(315>=ang2>225):
            x2=x2+3
            y2=y2+3
        elif(225>=ang2>135):
            x2=x2-3
            y2=y2+3
        elif(135>=ang2>45):
            x2=x2-3
            y2=y2-3
        cond2=True
    if(screen.get_at((int(xline22), int(yline22))) == (255,255,255,255) and freeze2==False):
        if(360>=ang2>315 or 45>=ang2>0):
            x2=x2+3
            y2=y2+3
        elif(315>=ang2>225):
            x2=x2-3
            y2=y2+3
        elif(225>=ang2>135):
            x2=x2-3
            y2=y2-3
        elif(135>=ang2>45):
            x2=x2+3
            y2=y2-3
        cond2=True
    if(screen.get_at((int(xline23), int(yline23))) == (255,255,255,255) and freeze2==False):
        if(360>=ang2>315 or 45>=ang2>0):
            x2=x2-3
            y2=y2-3
        elif(315>=ang2>225):
            x2=x2+3
            y2=y2-3
        elif(225>=ang2>135):
            x2=x2+3
            y2=y2+3
        elif(135>=ang2>45):
            x2=x2-3
            y2=y2+3
        cond2=True
    if(screen.get_at((int(xline24), int(yline24))) == (255,255,255,255) and freeze2==False):
        if(360>=ang2>315 or 45>=ang2>0):
            x2=x2-3
            y2=y2+3
        elif(315>=ang2>225):
            x2=x2-3
            y2=y2-3
        elif(225>=ang2>135):
            x2=x2+3
            y2=y2-3
        elif(135>=ang2>45):
            x2=x2+3
            y2=y2+3
        cond2=True
            
    if(cond2==True):
        n2=100
        speed2=0
        cond2=False
        freeze2=True
    if(n2>0):
        if(n2>75 or 50>n2>25):
            rotate21=pygame.transform.rotate(car11,ang2)
            rotate_rect=rotate21.get_rect(center=car11.get_rect(center=(x2,y2)).center)
            screen.blit(rotate21,rotate_rect2)
        else:
            rotate22=pygame.transform.rotate(car22,ang2)
            rotate_rect=rotate22.get_rect(center=car22.get_rect(center=(x2,y2)).center)
            screen.blit(rotate22,rotate_rect2)
        n2=n2-1
    elif(n2==0):
        freeze2=False
        
    #Start/Finish point2
    if(140>x2>54 and 515>y2>500):
        check12=True
    if(x2>1000 and 100>y2>30 and check12==True):
        check12=False
        check2=True
    if(1100<x2<1125 and 772>y2>702 and check2==True):
        point2+=1
        check2=False

    '''block=pygame.draw.rect(screen,color,pygame.Rect(x,y,h,w)) #(x,y,height,width)
    block2=pygame.draw.rect(screen,color2,pygame.Rect(x2,y2,h,w))'''
    #pygame.draw.rect(screen,(255,255,255),pygame.Rect(150,150,30,30))
    font = pygame.font.SysFont("Arial", 36)
    points=str(point)
    points2=str(point2)
    textsurf = font.render("Player 1 Score: ", False, (255,255,255))
    txtsurf = font.render(points, False, (255,255,255))
    textsurf2 = font.render("Player 2 Score: ", False, (255,255,255))
    txtsurf2 = font.render(points2, False, (255,255,255))
    textsurf3 = font.render("Finish", False, (255,255,255))
    screen.blit(textsurf, (200,200))
    screen.blit(txtsurf, (410,200))
    screen.blit(textsurf2, (200,250))
    screen.blit(txtsurf2, (410,250))
    screen.blit(textsurf3, (1050,660))
    font = pygame.font.SysFont("Arial", 100)
    if(point==round):
        text = font.render("Player 1 Wins!", False, (0,255,0))
        screen.blit(text, (480,350))
    elif(point2==round):
        text = font.render("Player 2 Wins!", False, (255,255,0))
        screen.blit(text, (480,350))
    pygame.display.update()
    fpsclock.tick(fps)
    if(point==round or point2==round):
        n=input("Do you want to quit? (Y/N): ")
        if(n.upper()=="Y"):
            run=False
pygame.quit()
