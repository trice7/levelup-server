"""View module for handling requests about events"""
from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from levelupapi.models import Event, Game, Gamer, EventGamer
from rest_framework.decorators import action

class EventView(ViewSet):
    """Level Up Event view"""
    
    def retrieve(self, request, pk):
        """Handle GET requests for single event
        
        Returns:
            Response -- JSON serialized game type
        """
        try:
          event = Event.objects.get(pk=pk)
          serializer = EventSerializer(event)
          return Response(serializer.data)
        except Event.DoesNotExist as ex:
          return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)
        
      
    def list(self, request):
        """Handle GET reqeusts to get all events
        
        Returns:
            Response -- JSON serialized list of events
        """
        events = Event.objects.all()
        
        #Query a specific game
        game = request.query_params.get('game', None)
        if game is not None:
          events = events.filter(game_id = game) #game_id is the foreign key in the Game class.
          
        uid = request.META['HTTP_AUTHORIZATION']
        gamer = Gamer.objects.get(uid=uid)
        
        for event in events:
          # Check to see if there is a row in the Event Games table that has the passed in gamer and event
          event.joined = len(EventGamer.objects.filter(gamer=gamer, event=event)) > 0
        
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)
      
    def create(self, request):
      """Handle POST orderations

      Returns:
          Response -- JSON serialized event instance
      """
      game = Game.objects.get(pk=request.data["gameId"])
      organizer = Gamer.objects.get(uid=request.data["userId"])
      
      event = Event.objects.create(
        description = request.data["description"],
        date = request.data["date"],
        time = request.data["time"],
        game = game,
        organizer = organizer,
      )
      
      serializer = EventSerializer(event)
      return Response(serializer.data)
    
    def update(self, request, pk):
      """Handle PUT requests for events

      Returns:
          Response -- Empty body with 204 status code
      """
      
      event = Event.objects.get(pk=pk)
      event.description = request.data['description']
      event.date = request.data['date']
      event.time = request.data['time']
      game = Game.objects.get(pk=request.data['gameId'])
      event.game = game
      organizer = Gamer.objects.get(uid=request.data['userId'])
      event.organizer = organizer
      event.save()
      
      return Response(None, status=status.HTTP_204_NO_CONTENT)
    
    def destroy(self, request, pk):
      event = Event.objects.get(pk=pk)
      event.delete()
      return Response(None, status=status.HTTP_204_NO_CONTENT)
    
    @action(methods=['post'], detail=True)
    def signup(self, request, pk):
      """Post request for a user to sign up for an event"""

      gamer = Gamer.objects.get(uid=request.data["userId"])
      event = Event.objects.get(pk=pk)
      attendee = EventGamer.objects.create(
          gamer=gamer,
          event=event
      )
      return Response({'message': 'Gamer added'}, status=status.HTTP_201_CREATED)
    
    @action(methods=['delete'], detail=True)
    def leave(self, request, pk):
      """Delete request for a user to leave an event"""
      event = Event.objects.get(pk=pk)
      gamer = Gamer.objects.get(uid=request.data["userId"])
      attendee = EventGamer.objects.get(gamer=gamer)
      attendee.delete()
      
      return Response({'message': 'Gamer left the event'}, status=status.HTTP_204_NO_CONTENT)
    
    @property
    def joined(self):
     return self.__joined

    @joined.setter
    def joined(self, value):
        self.__joined = value
      
      
class EventSerializer(serializers.ModelSerializer):
    """JSON serializer for game types"""
    class Meta:
        model= Event
        fields = ('id', 'game', 'description', 'date', 'time', 'organizer', 'joined')
        depth = 1
