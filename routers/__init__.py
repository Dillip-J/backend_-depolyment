# routers/__init__.py

# Active Auth Routers
from .auth import router as auth
from .provider_auth import router as provider_auth
from .admin_auth import router as admin_auth

# Active Core Routers
from .users import router as users
from .providers import router as providers
from .admin import router as admin
from .booking import router as booking
from .home import router as home

# Active Utility/Feature Routers
from .upload import router as upload
from .websockets import router as websockets
from .meet import router as meet

# 🚨 DEAD ROUTERS (Commented out because we dropped these tables from the DB)
# from .records import router as records       # (MedicalRecord table dropped)
# from .reviews import router as reviews       # (Review table dropped)
# from .complaints import router as complaints # (Complaint table dropped)
# from .feedback import router as feedback     # (Redundant/Dropped)
# from .support import router as support       # (Usually tied to Complaints)
# from .services import router as services     # (Merged into providers.py)

# # routers/__init__.py
# from .auth import router as auth
# from .booking import router as booking
# from .home import router as home
# from .records import router as records
# from .support import router as support
# # from .services import router as services
# from .feedback import router as feedback
# from .admin import router as admin
# from .admin_auth import router as admin_auth
# from .providers import router as providers
# from .upload import router as upload
# from .users import router as users
# from .websockets import router as websockets
# from .reviews import router as reviews
# from .complaints import router as complaints
# from .provider_auth import router as provider_auth
# from .meet import router as meet