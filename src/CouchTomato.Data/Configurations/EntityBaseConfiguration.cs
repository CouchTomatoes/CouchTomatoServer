using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using CouchTomato.Data.Entities;

namespace CouchTomato.Data.Configurations;

public abstract class EntityBaseConfiguration<T> : IEntityTypeConfiguration<T>
    where T : class, IEntityBase
{
    public virtual void Configure(EntityTypeBuilder<T> builder)
    {
        builder.HasKey(e => e.KeyID);
        builder.Property(x => x.ID).ValueGeneratedOnAdd();
        builder.Property(x => x.IsDeleted).HasDefaultValue(false);
        builder.Property(x => x.CreatedDate).HasColumnType("datetime2");
        builder.Property(x => x.ModifiedDate).HasColumnType("datetime2");
    }
}
