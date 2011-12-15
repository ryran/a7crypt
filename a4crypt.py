#!/usr/bin/env python
# a4crypt v0.4 last mod 2011/12/15
# Latest version at <http://github.com/ryran/pythonpractice>
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

# TODO: SCRIPT docstring.

# Methods that are imported when they're needed:
    #from os.path import exists
    #from tempfile import TemporaryFile, NamedTemporaryFile
    #from subprocess import Popen, PIPE, STDOUT
    #from getpass import getpass

class a4crypt:

    """Provide cmdline wrapper for symmetric {en,de}cryption functions of GPG.
    
    This simply aims to make GPG1/GPG2 symmetric ASCII encryption in terminals
    easier and more fun. (Actually, this was just an excuse for a project in my
    first week of learning python, but hey. ...)
    
    The most important method is main() -- it will launch an interactive prompt
    and take care of everything.
    
    Call disable_colors() if you like spam and wish all parrots were dead.
    
    launch_gpg() does the actual encryption/decryption, and you CAN call it
    directly: first save your input to the inputdata variable (file-objects
    welcome; lists are not), then run:
        launch_gpg(MODE, PASSFILE)
    where MODE is either e or d and PASSFILE is the path to a file containing
    only your passphrase. Grab your output from the gpg_output variable.
    
    It would of course be simpler and more secure to just let main() do that
    for you, since it would save the passphrase to a tempfile only readable by
    you, and would delete it as soon as the encryption or decryption is done,
    usually only seconds after the file was created. ... But suit yourself.
    
    """

    def __init__(self, colors='yes'):
        """Define vars we need, incl. colors. Check for GPG or GPG2."""
        self.inputdata = ''
        self.gpg_output = ''
        self.cRSET = '\033[0m'
        self.cBOLD = '\033[0m\033[1m'
        self.cRED = '\033[1;31m'
        self.cBLU = '\033[1;34m'
        self.cGRN = '\033[1;32m'
        self.cCYA = '\033[0;36m'
        if colors is 'no':
            self.disable_colors()
        # Time to check for gpg or gpg2 and set variables accordingly
        # TODO: Should be checking for apps using some bin or PATH variable
        #       instead of hardcoding '/usr/bin/' .. need to find The Right Way
        from os.path import exists
        programs=('gpg', 'gpg2')
        for program in programs:
            if exists('/usr/bin/'+program):
                break
        else:
            print(self.cRED +
                  "Error! This program requires either gpg or gpg2 to work!" +
                  self.cRSET)
            exit()
        if program == 'gpg':
            self.gpg = 'gpg'
        else:
            self.gpg = 'gpg2'


    def disable_colors(self):
        """Set all color variables to null to disable coloring of output."""
        self.cRSET = ''
        self.cBOLD = ''
        self.cRED = ''
        self.cBLU = ''
        self.cGRN = ''
        self.cCYA = ''

        
    def main(self):
        """Load initial prompt and kick off all the other functions."""
        # Initial prompt
        print(self.cBOLD + "[" + self.cRED + "e" + self.cBOLD + "]ncrypt, [" +
              self.cRED + "d" + self.cBOLD + "]ecrypt, or [" + self.cRED +
              "q" + self.cBOLD + "]uit?")
        mode = raw_input(": " + self.cRSET)
        mode = self.test_prompt(mode, 'e', 'd', 'Q', 'q')

        if mode == 'q' or mode == 'Q':
            if __name__ == "__main__":
                exit()
            return
        # ENCRYPT MODE
        elif mode == 'e':
            # Get our message-to-be-encrypted from the user; save to variable
            print(self.cBLU + "Type or paste message to be encrypted.\n" +
                  "End with line containing only a triple-semicolon, i.e. " +
                  self.cBOLD + ";;;" + self.cBLU + "\n:" + self.cRSET),
            self.inputdata = self.multiline_input(';;;')
            print
            # Get passphrase from the user; save to tmpfile
            pwd = self.get_passphrase()
            from tempfile import TemporaryFile, NamedTemporaryFile
            passphrasefile = NamedTemporaryFile(bufsize=0)
            passphrasefile.write(pwd)
            # Launch our subprocess and print the output
            self.launch_gpg(mode, passphrasefile.name)
            passphrasefile.close()
            print(self.cGRN + "\nEncrypted message follows:\n\n" + self.cCYA +
                  self.gpg_output + self.cRSET)
        # DECRYPT MODE
        elif mode == 'd':
            # Get our encrypted message from the user; save to variable
            print(self.cBLU + "Paste GPG-encrypted message to be decrypted." +
                  "\n:" + self.cRSET),
            self.inputdata = self.multiline_input('-----END PGP MESSAGE-----',
                                                  keeplastline='yes')
            print
            # Get passphrase from the user; save to tmpfile
            pwd = self.get_passphrase(prompt='once')
            from tempfile import TemporaryFile, NamedTemporaryFile
            passphrasefile = NamedTemporaryFile(bufsize=0)
            passphrasefile.write(pwd)
            # Launch our subprocess and print the output
            self.launch_gpg(mode, passphrasefile.name)
            passphrasefile.close()
            if len(self.gpg_output) == 0:
                print(self.cRED + "Error in decryption process!\n" + self.cRSET)
            else:
                print(self.cGRN + "\nDecrypted message follows:\n\n" +
                      self.cCYA + self.gpg_output + self.cRSET + "\n")


    def test_prompt(self, INPUT, *args):
        """Test user input. Keep prompting until recieve one of 'args'."""
        while True:
            for desired in args:
                if INPUT == desired:
                    return INPUT
                else:
                    continue
            else:
                print(self.cRED + "Expecting one of {}" + self.cRSET) .format(args)
                INPUT = raw_input(self.cBOLD + ": " + self.cRSET)


    def multiline_input(self, EOFstr, keeplastline='no'):
        """Prompt for (and return) multiple lines of raw input.
        
        Stop prompting once receive a line containing only EOFstr. Return input
        minus that last line, unless run with keeplastline=yes.
        """
        userinput = []
        userinput.append(raw_input())
        while userinput[-1] != EOFstr:
            userinput.append(raw_input())
        if keeplastline is 'no':
            userinput.pop()
        return "\n".join(userinput)


    def get_passphrase(self, prompt='twice'):
        """Prompt for a passphrase until user enters something twice.
        
        Skip the second confirmation prompt if run with prompt=once.
        """
        from getpass import getpass
        while True:
            pwd1 = getpass(prompt=self.cBLU +
                           "Carefully enter passphrase: " + self.cRSET)
            while len(pwd1) == 0:
                pwd1 = getpass(prompt=self.cRED +
                               "You must enter a passphrase: " + self.cRSET)
            if prompt is 'once':
                return pwd1
            pwd2 = getpass(prompt=self.cBLU +
                           "Repeat passphrase to confirm: " + self.cRSET)
            if pwd1 == pwd2:
                return pwd1
            print(self.cRED + "The passphrases you entered did not match" +
                  self.cRSET)


    def launch_gpg(self, MODE, PASSFILE, returnoutput='no'):
        """Start our GPG or GPG2 subprocess & save/return its output."""
        from subprocess import Popen, PIPE, STDOUT
        if MODE is 'e':
            g = Popen([self.gpg, '--no-use-agent', '--batch', '--no-tty',
                      '--yes', '-a', '-c', '--force-mdc', '--passphrase-file',
                      PASSFILE], stdin=PIPE, stdout=PIPE)
        elif MODE is 'd':
            g = Popen([self.gpg, '--no-use-agent', '--batch', '--no-tty',
                      '--yes', '-d', '--passphrase-file',
                      PASSFILE], stdin=PIPE, stdout=PIPE)
        else:
            return "Improper MODE specified. Must be one of 'e' or 'd'."
        self.gpg_output = g.communicate(input=self.inputdata)[0]
        if returnoutput is 'yes':
            return self.gpg_output
        # In the interest of efficiency, I prefer to save the output to a class
        # variable, instead of returning it. 



# BEGIN
if __name__ == "__main__":

    from sys import argv
    if len(argv) == 2 and argv[1] == 'nocolor':
        a4 = a4crypt(colors='no')
    elif len(argv) == 1:
        a4 = a4crypt()
    else:
        print("Run with no arguments to get interactive prompt.\n" +
              "Or if you've already done that, fyi there's an optional arg\n" +
              "of 'nocolor', which should be pretty self-explanatory.")
        exit()
    while True:
        a4.main()

