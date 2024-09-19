import boto3

class S3:
    """Provide a common, convenient cloud API wrapper for S3
    """

    def __init__(self, *, name=None, key=None, role=None, external_id=None, region_name=None) -> None:
        # use name if we are accessing from vault or a key management system
        self.s3_connection = None

        if name or key:
            self._create_s3_session(
                name=name,
                key=key,
                role=role,
                external_id=external_id,
                region_name=region_name,
            )

    def _create_s3_session(
        self, *, name=None, key=None, role=None, external_id=None, region_name=None
    ):
        """Create and authenticate our cloud storage provider API.

        Can take either arbitrary keys or a key registered in :py:mod:`bias`'
        config file.
        """
        global _credential_cache
        access_key = None
        secret_key = None
        if name is not None:
            pass
            # if not (access_and_secret_keys := _credential_cache.get(name)):
            #     access_and_secret_keys = get_vault_secret(f"s3/{name}")
            #     _credential_cache[name] = access_and_secret_keys
            # secret_key = access_and_secret_keys['secret_key']
            # access_key = access_and_secret_keys['access_key']
        elif name is None and key is not None:
            secret_key = key['secret_key']
            access_key = key['access_key']
        self.boto_session = boto3.Session(
            access_key, secret_key, region_name=region_name
        )

        if role:
            # Use STS to assume a different role.
            sts = self.boto_session.client('sts')
            assumed = sts.assume_role(
                RoleArn=role, RoleSessionName='LciKasarani', ExternalId=external_id
            )
            self.boto_session = boto3.Session(
                assumed['Credentials']['AccessKeyId'],
                assumed['Credentials']['SecretAccessKey'],
                assumed['Credentials']['SessionToken'],
            )

        self.s3_connection = self.boto_session.resource('s3')
