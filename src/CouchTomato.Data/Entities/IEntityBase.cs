namespace CouchTomato.Data.Entities;

public interface IEntityBase
{
    Guid ID { get; set; }
    long KeyID { get; set; }
    DateTime CreatedDate { get; set; }
    DateTime ModifiedDate { get; set; }
    long? CreatedDateUnix { get; set; }
    long? ModifiedDateUnix { get; set; }
    Guid? CreatedBy { get; set; }
    bool IsDeleted { get; set; }
}
