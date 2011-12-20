#!/usr/bin/env python
# a4crypt v0.5.4 last mod 2011/12/21
# Latest version at <http://github.com/ryran/a7crypt>
# Copyright 2011 Ryan Sawhill <ryan@b19.org>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License <gnu.org/licenses/gpl.html> for more details.
#------------------------------------------------------------------------------

# TODO: SCRIPT docstring
# TODO: Implement GPG reading passphrase from fd instead of tempfile with 
# --passphrase-fd or --command-fd (will have to also make data use that method)

# Standard Library stuff only
from os.path import isfile
from os import environ, pathsep, access, X_OK
from collections import namedtuple
from getpass import getpass
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE, STDOUT


class a4crypt:

    """Provide cmdline wrapper for symmetric {en,de}cryption functions of GPG.
    
    This simply aims to make GPG1/GPG2 symmetric ASCII encryption in terminals
    easier and more fun. (Actually, this was just an excuse for a project in my
    first week of learning python, but hey. ...)
    
    Instantiate this class with color=False if you like spam.
    
    The most important method here is main() -- it will launch an interactive
    prompt and take care of everything for you. That said, you can set the
    proper attribute or two and launch the processing method yourself. ...
    
    And that method would be launch_gpg() which does the actual encryption &
    decryption. To use it directly, first save your input to self.inputdata
    (simple text or file-objects welcome; lists are not), then run:
        launch_gpg(mode, passfile)
    where mode is either e or d and passfile is the path to a file containing
    only your passphrase.
    
    It would of course be simpler and more secure to just let main() do that
    for you, since it would save the passphrase to a tempfile only readable by
    you, and would delete it as soon as the encryption or decryption is done,
    usually only seconds after the file was created. ... But suit yourself.
    
    """

    def __init__(self, color=True):
        """Define vars we need, incl. colors. Check for GPG or GPG2."""
        self.inputdata = ''
        Colors = namedtuple('Colors', 'RST BLD R B G C')
        if color:
            self.c = Colors(
                RST='\033[0m', BLD='\033[0m\033[1m', R='\033[1;31m',
                B='\033[1;34m', G='\033[1;32m', C='\033[0;36m')
        else:
            self.c = Colors('', '', '', '', '', '')

        # Time to check for gpg or gpg2 and set variables accordingly
        for d in environ['PATH'] .split(pathsep):
            for p in ('gpg', 'gpg2'):
                if isfile(d+'/'+p) and access(d+'/'+p, X_OK):
                    self.gpg = p
                    return
        else:
            print("{R}Error! This program requires gpg or gpg2 to work!{RST}"
                  .format(**self.c._asdict()))
            if __name__ == "__main__": exit()
            return



    def main(self):
        """Load initial prompt and kick off all the other functions."""
        # Initial prompt
        print("{BLD}[{R}e{BLD}]ncrypt, [{R}d{BLD}]ecrypt, or [{R}q{BLD}]uit?"
              .format(**self.c._asdict()))
        mode = self.test_rawinput(": ", 'e', 'd', 'Q', 'q')

        if mode in {'q', 'Q'}:
            if __name__ == "__main__":
                exit()
            return
        # ENCRYPT MODE
        elif mode == 'e':
            # Get our message-to-be-encrypted from the user; save to variable
            print("{B}Type or paste message to be encrypted.\nEnd with line "
                  "containing only a triple-semicolon, i.e. {BLD};;;{B}\n:{RST}"
                  .format(**self.c._asdict())),
            self.inputdata = self.multiline_input(';;;')
            print
            # Get passphrase from the user; save to tmpfile
            pwd = self.get_passphrase()
            #from tempfile import NamedTemporaryFile
            passphrasefile = NamedTemporaryFile(bufsize=0)
            passphrasefile.write(pwd)
            # Launch our subprocess and print the output
            gpg_output = self.launch_gpg(mode, passphrasefile.name)
            passphrasefile.close()
            print("{0.G}\nEncrypted message follows:\n\n{0.C}{1}{0.RST}"
                  .format(self.c, gpg_output))
        # DECRYPT MODE
        elif mode == 'd':
            # Get our encrypted message from the user; save to variable
            print("{0.B}Paste GPG-encrypted message to be decrypted.\n:{0.RST}"
                  .format(self.c)),
            self.inputdata = self.multiline_input('-----END PGP MESSAGE-----',
                                                  keeplastline=True)
            print
            # Get passphrase from the user; save to tmpfile
            pwd = self.get_passphrase(confirm=False)
            #from tempfile import NamedTemporaryFile
            passphrasefile = NamedTemporaryFile(bufsize=0)
            passphrasefile.write(pwd)
            # Launch our subprocess and print the output
            gpg_output = self.launch_gpg(mode, passphrasefile.name)
            while True:
                if gpg_output:
                    print("{0.G}\nDecrypted message follows:\n\n{0.C}{1}"
                          "{0.RST}\n" .format(self.c, gpg_output))
                    break
                else:
                    print("{0.R}Error in decryption process! Try again with a "
                          "different passphrase?" .format(self.c))
                    tryagain = self.test_rawinput("[y/n]: ", 'y', 'n')
                    if tryagain == 'y':
                        pwd = self.get_passphrase(confirm=False)
                        passphrasefile.seek(0)
                        passphrasefile.write(pwd)
                        gpg_output = self.launch_gpg(mode, passphrasefile.name)
                    else:
                        break
            passphrasefile.close()                



    def test_rawinput(self, prompt, *args):
        """Test user input. Keep prompting until recieve one of 'args'."""
        prompt = self.c.BLD + prompt + self.c.RST
        userinput = raw_input(prompt)
        while userinput not in args:
            userinput = raw_input("{0.R}Expecting one of {1}\n{2}"
                                  .format(self.c, args, prompt))
        return userinput

    def multiline_input(self, EOFstr, keeplastline=False):
        """Prompt for (and return) multiple lines of raw input.
        
        Stop prompting once receive a line containing only EOFstr. Return input
        minus that last line, unless run with keeplastline=True.
        """
        userinput = []
        userinput.append(raw_input())
        while userinput[-1] != EOFstr:
            userinput.append(raw_input())
        if not keeplastline:
            userinput.pop()
        return "\n".join(userinput)


    def get_passphrase(self, confirm=True):
        """Prompt for a passphrase until user enters something twice.
        
        Skip the second confirmation prompt if run with confirm=False.
        """
        #from getpass import getpass
        while True:
            pwd1 = getpass(prompt="{B}Carefully enter passphrase:{RST} "
                           .format(**self.c._asdict()))
            while len(pwd1) == 0:
                pwd1 = getpass(prompt="{R}You must enter a passphrase:{RST} "
                               .format(**self.c._asdict()))
            if not confirm:
                return pwd1
            pwd2 = getpass(prompt="{B}Repeat passphrase to confirm:{RST} "
                           .format(**self.c._asdict()))
            if pwd1 == pwd2:
                return pwd1
            print("{R}The passphrases you entered did not match!{RST}"
                  .format(**self.c._asdict()))


    def launch_gpg(self, mode, passfile):
        """Start our GPG or GPG2 subprocess & save/return its output."""
        #from subprocess import Popen, PIPE, STDOUT
        if mode == 'e':
            g = Popen([self.gpg, '--no-use-agent', '--batch', '--no-tty',
                      '--yes', '-a', '-c', '--force-mdc', '--passphrase-file',
                      passfile], stdin=PIPE, stdout=PIPE)
        elif mode == 'd':
            g = Popen([self.gpg, '--no-use-agent', '--batch', '--no-tty',
                      '--yes', '-d', '--passphrase-file',
                      passfile], stdin=PIPE, stdout=PIPE)
        else:
            return "Improper mode specified. Must be one of 'e' or 'd'."
        return g.communicate(input=self.inputdata)[0]



# BEGIN
if __name__ == "__main__":

    from sys import argv
    if len(argv) == 2 and argv[1] == 'nocolor':
        a4 = a4crypt(color=False)
    elif len(argv) == 1:
        a4 = a4crypt()
    else:
        print("Run with no arguments to get interactive prompt.\n"
              "Or if you've already done that, fyi there's an optional arg\n"
              "of 'nocolor', which should be pretty self-explanatory.")
        exit()

    while True:
        a4.main()

