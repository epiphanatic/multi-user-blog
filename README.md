# multi-user-blog
Multi-user blog written in Python. Allows registered / logged in users to make posts, as well as comment on and like posts.

# Dependencies

You must have python installed in order to start the site

See instructions [here](https://classroom.udacity.com/nanodegrees/nd004/parts/0041345401/modules/356120945175460/lessons/990110642/concepts/36256587390923#) for Mac.

See instructions [here](https://classroom.udacity.com/nanodegrees/nd004/parts/0041345401/modules/356120945175460/lessons/990110642/concepts/36691786570923#) for Windows.

# Viewing the blog on Google Cloud Platform

Visit the live blog [here](http://fswd-user-blog.appspot.com/blog).

# Starting the app on your local machine

1) Clone this repository or download the zip file.

2) Install Google App Engine SDK. Directions for doing so can be found [here](https://cloud.google.com/appengine/docs/standard/python/download).

3) In a command line, go to the project directory on your computer (wherever your cloned it to, or extracted the zip file) and type:
```
gcloud app browse
```

This will launch the application on Google Cloud Platform.

Alternatively, if you want to actually run the app (as opposed to just starting it) on your local machine, you can do this by:

1) Install Google App Engine SDK as above.

2) Ensure that your IDE recognizes the SDK or has it built in. PyCharm is one example of an IDE that indeed does this.

3) Run the application like you would run any other Python app in your IDE and go to the port on localhost that the logs say the application is running on (this is normally localhost:8080)

