# Mistral Operator 

We participate to the mistral hackaton

We want a system that use mistral model and solve simple tasks like summarizing mail with computer use.
We have 6 diferents agents for this system : 
    
  1.interaction with user
  
  2.parser
  
  3.information:

        i. info gathering for understanding of how to perform tasks: if i ask it for usage in specific apps, it needs to understand how to use it - it has access to the web
        ii. information gathering from the user (also asks for permissions)

4. basic task performer - takes the parser's commands and performs the tasks

5. typing/creation - writes mails, etc.

6. an overseer - it oversees all the tasks and tells the other 5 models how to work and also solves problems
