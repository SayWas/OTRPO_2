import uuid

import pyotp


def generate_otp():
    totp = pyotp.TOTP(pyotp.random_base32())
    return totp.now()


async def set_otp_to_redis(user_id, otp, redis):
    await redis.set(f"otp:{user_id}", otp, ex=300)


async def verify_otp_from_redis(user_id: uuid.UUID, otp: str, redis):
    stored_otp = await redis.get(f"otp:{user_id}")
    if not stored_otp or stored_otp != otp:
        return None
    await redis.delete(f"otp:{user_id}")
    return True
