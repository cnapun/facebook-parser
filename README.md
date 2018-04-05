# facebook-parser
Script to parse Facebook Messages from an archive. Initialize the parser with the path to the `messages.htm` file in the archive. 
The current functions offer simple statistics, but the main goal of this is to make it easy to open up a Jupyter Notebook and plot relationships that seem interesting.

Facebook recently changed the archive format, so now instead of specifying the `messages.htm` file, the base path of all the separate message html files must be specified. (for example, `facebook-johndoe/messages`). the script matches any file that is of the form `facebook-johndoe/messages/(integer).html`
