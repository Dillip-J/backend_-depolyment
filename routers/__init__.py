# routers/__init__.py
from .auth import router as auth
from .booking import router as booking
from .home import router as home
from .records import router as records
from .support import router as support
from .services import router as services
from .feedback import router as feedback
from .admin import router as admin
from .admin_auth import router as admin_auth
from .providers import router as providers
from .upload import router as upload
from .users import router as users
from .websockets import router as websockets
from .reviews import router as reviews
from .complaints import router as complaints
from .doctor_bookings import router as doctor_bookings