# This file looks for new folder inside user uploads and convert them to reel, if they are not already converted

import os


def text_to_audio(folder):
    print("TTA - " ,folder)

def create_reel(folder):
    print("CR - " , folder)

if __name__ == "__main__":
    with open("done.txt", "r") as f:
        done_folders = f.readlines()
    
    done_folders = [f.strip() for f in done_folders ]
    folders = os.listdir("user_uploads")
    print(folders, done_folders)
    for folder in folders:
        if(folder not in done_folders):
            text_to_audio(folder) # Generate the audio.mp3 from desc.txt
            create_reel(folder) # convert images and audio inside teh folder to a reel
            with open("done.txt", "a") as f:
                f.write(folder + "\n")
        
        
    












